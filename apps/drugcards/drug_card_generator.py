"""
drug_card_generator.py
=======================

Pure generation logic for nursing drug cards, using the OpenAI API.

This module has ZERO web-framework code in it (no Flask, no request/response
objects). It can be imported and used from app.py, a CLI script, a test
file, a Jupyter notebook, etc. Its only job: given a drug name, return a
validated Python dict matching the drug-card schema.

Public functions:
    get_drug_card(drug_name, use_cache=True) -> dict
    call_openai_for_drug_card(drug_name) -> dict
    extract_json(raw_text) -> dict
    normalize_card(data, requested_drug_name) -> dict
"""

import os
import re
import json
import logging
from html import unescape
from functools import lru_cache
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIStatusError, APIConnectionError

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drug-card-generator")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY is not set. Set it in your .env file before "
        "making real requests."
    )

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# --------------------------------------------------------------------------
# Quick-pick drug list (shared constant — imported by app.py for the UI)
# --------------------------------------------------------------------------

QUICK_PICK_DRUGS = [
    "Metformin", "Furosemide", "Heparin",
    "Insulin", "Warfarin", "Morphine",
    "Lisinopril", "Digoxin", "Metoprolol",
    "Aspirin", "Amoxicillin", "Atorvastatin",
]

# --------------------------------------------------------------------------
# System prompt: defines the "STEM RN Pharmacology AI" persona + strict
# JSON output contract so the frontend can render it deterministically.
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are STEM RN Pharmacology AI.

You generate premium nursing drug cards for nursing students and nurses
studying for the NCLEX. You focus on NURSING responsibilities (assessment,
administration, monitoring, patient education) rather than physician
prescribing decisions.

You can handle broad medicine lookups, not just exact generic drug names.
If the user gives a brand name, generic name, abbreviation, OTC medicine,
combination product, partial name, common misspelling, or a short medicine
question, infer the most likely medicine and generate the best matching card.
If the input is ambiguous, use the most likely single medicine match and
state that assumption briefly in clinical_tips.
If web search context is provided, use it as the primary fallback source for
uncertain or unfamiliar medicines.

You must respond with ONLY a single valid JSON object — no markdown code
fences, no commentary before or after, no trailing commas. The JSON must
match this exact schema (all fields are strings unless noted otherwise;
use "" or [] when a field genuinely does not apply, do not omit fields):

{
  "drug_name": "Generic name, e.g. Amoxicillin",
  "brand_names": "Comma separated brand names, e.g. Amoxil, Trimox",
  "drug_class": "Drug class / category, e.g. Aminopenicillin / Beta-Lactam Antibiotic",
  "pregnancy_category": "e.g. B — Generally considered safe; commonly used in pregnancy (empty string if not applicable)",
  "route_of_administration": "e.g. PO, IV, IM, SubQ, Topical — list all relevant routes",
  "black_box_warning": "Full black box warning text, or empty string if none",
  "mechanism_of_action": "2-4 sentence explanation in plain nursing-relevant language",
  "indications": ["array of indication strings, most common first"],
  "contraindications": ["array of contraindication / caution strings"],
  "side_effects": [
    {"system": "e.g. GI", "effects": "e.g. Nausea, vomiting, diarrhea, C. difficile colitis (any antibiotic)"}
  ],
  "serious_adverse_effects": ["array of serious/emergent adverse effect strings, most dangerous first"],
  "assessment_before_administration": ["array of pre-administration assessment items"],
  "monitoring_during_therapy": ["array of monitoring parameters during therapy"],
  "nursing_considerations": ["array of nursing considerations / administration tips"],
  "patient_education": ["array of patient teaching points"],
  "nclex_pearls": ["array of short, high-yield NCLEX exam pearls, each under ~12 words"],
  "memory_trick": "One memorable mnemonic or memory device as a single string",
  "clinical_tips": ["array of 1-3 concise real-world clinical tips for nurses"]
}

Guidelines:
- Treat every field in the schema as a required drug-card section. Populate all clinically applicable sections; use "" or [] only when a section genuinely does not apply to the requested drug.
- Treat the user's text as a medicine search query when needed. Resolve it to the most likely medicine name before generating the card, and include that resolved name in drug_name.
- Be clinically accurate and concise. Bullet-style phrases, not paragraphs, for array fields.
- Prioritize bedside nursing responsibilities: assessment, safe administration, monitoring, hold/notify parameters, escalation, and patient teaching. Do not provide prescriber-oriented dosing or treatment-selection recommendations.
- If the user mentions what they need the medicine for, reflect that in the relevant sections, but keep the output centered on nursing-drug-card information.
- Put the most important safety point first in each section. Prefix immediately life-threatening or urgent nursing actions with "CRITICAL:" so the UI can emphasize them.
- Structure information for table-based display whenever possible. Keep each side-effect row limited to one body system and concise effects for that system.
- side_effects should be grouped by body system (GI, CNS, Cardiovascular, Dermatologic, Hematologic, Renal, Respiratory, etc.) — only include systems relevant to the drug.
- serious_adverse_effects should highlight true emergencies (e.g. anaphylaxis, Stevens-Johnson syndrome, agranulocytosis) — these will be shown in a red warning box.
- nclex_pearls should be the kind of short factoids that show up as NCLEX distractors/answers.
- If the drug has no black box warning, return an empty string for black_box_warning — do NOT invent one.
- If pregnancy category is not clinically relevant (e.g. topical drug, pediatric-only), return an empty string.
- Always return strictly valid JSON parseable by json.loads with no surrounding text.
"""

USER_PROMPT_TEMPLATE = (
    "Generate a complete nursing drug card for this medicine lookup: {drug_name}\n\n"
    "If the input is a brand name, OTC medicine, combo product, abbreviation, "
    "or a misspelled medicine name, resolve it to the most likely medicine "
    "before generating the card. If the query is broad or slightly vague, "
    "infer the closest single medicine and note the assumption briefly in "
    "clinical_tips.\n\n"
    "Remember: respond with ONLY the JSON object matching the schema, nothing else."
)

WEB_SEARCH_LIMIT = int(os.getenv("MED_LOOKUP_SEARCH_LIMIT", "3"))
WEB_SEARCH_TIMEOUT = float(os.getenv("MED_LOOKUP_SEARCH_TIMEOUT", "5"))

# Fields that must always be lists in the final card.
LIST_FIELDS = {
    "indications", "contraindications", "serious_adverse_effects",
    "assessment_before_administration", "monitoring_during_therapy",
    "nursing_considerations", "patient_education", "nclex_pearls",
    "clinical_tips",
}

DEFAULT_CARD_FIELDS = {
    "drug_name": "",
    "brand_names": "",
    "drug_class": "",
    "pregnancy_category": "",
    "route_of_administration": "",
    "black_box_warning": "",
    "mechanism_of_action": "",
    "indications": [],
    "contraindications": [],
    "side_effects": [],
    "serious_adverse_effects": [],
    "assessment_before_administration": [],
    "monitoring_during_therapy": [],
    "nursing_considerations": [],
    "patient_education": [],
    "nclex_pearls": [],
    "memory_trick": "",
    "clinical_tips": [],
}


# --------------------------------------------------------------------------
# Pure helper functions (no network calls) — easy to unit test in isolation
# --------------------------------------------------------------------------

def extract_json(raw_text: str) -> dict:
    """
    Defensively extract a JSON object from a model response.

    Called by call_openai_for_drug_card immediately after OpenAI returns text.
    Call it directly only to convert a raw model response into a dictionary.

    Handles the common failure modes: the model wrapping the JSON in
    ```json ... ``` fences, or adding a stray sentence before/after the
    object. Raises ValueError/json.JSONDecodeError if no valid JSON object
    can be recovered.
    """
    text = raw_text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    return json.loads(text)


def web_search_medicine_context(query: str) -> str:
    """
    Pull a few short web search snippets so the model can answer uncertain
    medicine lookups with fresher context.

    Uses DuckDuckGo's HTML results page to avoid any extra API key.
    If search fails, returns an empty string and the model falls back to its
    own medical knowledge.
    """
    cleaned = (query or "").strip()
    if not cleaned:
        return ""

    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(cleaned + ' medicine drug')}"
    request = Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    try:
        with urlopen(request, timeout=WEB_SEARCH_TIMEOUT) as response:
            html_text = response.read().decode("utf-8", errors="ignore")
    except (URLError, HTTPError, TimeoutError, ValueError) as e:
        logger.info("Web search skipped for %r: %s", cleaned, e)
        return ""

    snippets = []
    for block in re.finditer(
        r'<a[^>]+class="result__a"[^>]*>(.*?)</a>.*?result__snippet[^>]*>(.*?)</a>',
        html_text,
        re.DOTALL,
    ):
        title_html, snippet_html = block.groups()
        title = re.sub(r"<.*?>", "", title_html)
        snippet = re.sub(r"<.*?>", "", snippet_html)
        title = unescape(re.sub(r"\s+", " ", title)).strip()
        snippet = unescape(re.sub(r"\s+", " ", snippet)).strip()
        if title or snippet:
            snippets.append(f"- {title}: {snippet}".strip())
        if len(snippets) >= WEB_SEARCH_LIMIT:
            break

    if not snippets:
        return ""

    return (
        "Web search context for this medicine lookup (use as supplemental grounding, not as direct citations):\n"
        + "\n".join(snippets)
    )


def normalize_card(data: dict, requested_drug_name: str) -> dict:
    """
    Fill in any missing keys with safe defaults so the frontend never
    crashes on a missing field, and make sure list fields are actually
    lists (guards against the model returning a string instead of an array).

    Called by call_openai_for_drug_card after JSON parsing. Call it directly
    when imported or test data must be made safe for the frontend.
    """
    merged = {**DEFAULT_CARD_FIELDS, **(data or {})}

    for field in LIST_FIELDS:
        value = merged.get(field)
        if isinstance(value, str):
            merged[field] = [v.strip(" -\t") for v in re.split(r"[\n;]+", value) if v.strip()]
        elif not isinstance(value, list):
            merged[field] = []

    side_effects = merged.get("side_effects")
    if not isinstance(side_effects, list):
        merged["side_effects"] = []
    else:
        cleaned = []
        for row in side_effects:
            if isinstance(row, dict) and "system" in row and "effects" in row:
                cleaned.append({
                    "system": str(row["system"]),
                    "effects": str(row["effects"]),
                })
        merged["side_effects"] = cleaned

    if not merged.get("drug_name"):
        merged["drug_name"] = requested_drug_name

    return merged


# --------------------------------------------------------------------------
# Network-calling functions
# --------------------------------------------------------------------------

def call_openai_for_drug_card(drug_name: str) -> dict:
    """
    Calls the OpenAI Chat Completions API with the pharmacology system
    prompt and returns the parsed, normalized drug card dict.

    Called by get_drug_card for refresh requests and by the internal cache on
    a cache miss. Call it directly only when a fresh API response is required.

    Raises RuntimeError with a user-friendly message on failure.
    """
    if client is None:
        raise RuntimeError(
            "Server is missing OPENAI_API_KEY. Add it to your .env file."
        )

    search_context = web_search_medicine_context(drug_name)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(drug_name=drug_name)},
    ]
    if search_context:
        messages.append({"role": "user", "content": search_context})

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
    except APIStatusError as e:
        logger.exception("OpenAI API returned an error status")
        raise RuntimeError(f"OpenAI API error: {e.status_code} — {e.message}") from e
    except APIConnectionError as e:
        logger.exception("Could not connect to OpenAI API")
        raise RuntimeError("Could not connect to OpenAI API. Check your network/API key.") from e
    except APIError as e:
        logger.exception("OpenAI API request failed")
        raise RuntimeError(f"OpenAI API request failed: {str(e)}") from e

    raw_text = response.choices[0].message.content or ""

    if not raw_text.strip():
        raise RuntimeError("Model returned an empty response.")

    try:
        data = extract_json(raw_text)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("Failed to parse model JSON. Raw response:\n%s", raw_text)
        raise RuntimeError("Model did not return valid JSON. Please try again.") from e

    return normalize_card(data, drug_name)


@lru_cache(maxsize=64)
def _cached_drug_card_json(drug_name_lower: str) -> str:
    """
    Internal cache layer keyed on the lowercased drug name. Stores a JSON
    string (lru_cache requires hashable/immutable return values, and dicts
    aren't hashable, so we cache the serialized form and json.loads it back
    in get_drug_card()).

    Called only by get_drug_card when use_cache=True. This is an internal
    helper and should not be called by routes or external modules.
    """
    card = call_openai_for_drug_card(drug_name_lower.title())
    return json.dumps(card)


def get_drug_card(drug_name: str, use_cache: bool = True) -> dict:
    """
    Public entry point. Validates input, optionally uses the in-process
    cache, and returns a plain dict matching the drug-card schema.

    Called by the /api/generate route whenever a user requests a drug card.
    This is the preferred function for all normal callers.

    Raises:
        ValueError   — invalid input (empty / too long)
        RuntimeError — API or parsing failure
    """
    cleaned = (drug_name or "").strip()
    if not cleaned:
        raise ValueError("Drug name must not be empty.")
    if len(cleaned) > 100:
        raise ValueError("Drug name is too long.")

    if use_cache:
        return json.loads(_cached_drug_card_json(cleaned.lower()))
    return call_openai_for_drug_card(cleaned)


def clear_cache() -> None:
    """
    Clear every drug card stored in the in-process LRU cache.

    Called by the /api/cache/clear admin route. Call it after prompt/schema
    changes or whenever subsequent requests must fetch fresh OpenAI data.
    """
    _cached_drug_card_json.cache_clear()
