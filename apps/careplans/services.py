"""
careplans/services.py

Reusable, backend-friendly functions for generating and editing nursing
"Care Plans" using the OpenAI API.

This module intentionally contains ONLY functions (no view/URL/CLI code) -
same design as care_plan_engine.py before this was folded into Django.
Django views in careplans/views.py import these functions and call them
directly, passing in the required inputs and receiving JSON-serializable
Python dicts back. No functional logic below this docstring was changed.

--------------------------------------------------------------------------
Two supported scenarios
--------------------------------------------------------------------------

1. Generate a NEW care plan
   care_plan = generate_care_plan(patient_input)

2. Edit an EXISTING care plan
   updated_care_plan = edit_care_plan(user_prompt, existing_care_plan)

   Internally this:
     a) Asks the LLM which top-level sections are affected by the request
        (identify_affected_sections)
     b) Extracts ONLY those sections from the existing care plan
        (extract_sections)
     c) Sends only the extracted sections + the user's edit prompt to the
        LLM to regenerate just those sections (generate_section_updates)
     d) Merges the regenerated sections back into the original care plan,
        leaving everything else untouched (merge_care_plan)

--------------------------------------------------------------------------
Care Plan JSON structure (matches the "Care Plan Builder" UI)
--------------------------------------------------------------------------
{
  "metadata": {
    "title": str,                       # e.g. "STEM RN CARE PLAN"
    "subtitle": str,                     # e.g. "Male — Chief Complaint / Reason for Admission"
    "nursing_diagnoses_count": int,
    "generated_at": str (ISO 8601)
  },
  "overview": {
    "patient_overview": str,
    "disease_overview": str,
    "priority_nursing_diagnoses_summary": [
      {"rank": int, "title": str, "subtitle": str}, ...
    ]
  },
  "assessment": {
    "subjective_data": [str, ...],
    "objective_data": [str, ...]
  },
  "diagnoses": [
    {
      "diagnosis": str,
      "related_to": str,
      "as_evidenced_by": [str, ...],
      "smart_goals": [
        {"goal": str, "timeframe": str, "met": bool}, ...
      ],
      "nursing_interventions": [
        {"intervention": str, "scientific_rationale": str}, ...
      ],
      "evaluation_criteria": [str, ...],
      "nclex_pearls": [str, ...]
    }, ...
  ],
  "medications": [
    {"medication": str, "dose": str, "route": str, "nursing_purpose": str}, ...
  ],
  "lab_findings": [
    {
      "lab_value": str,
      "patient_value": str,
      "normal_range": str,
      "clinical_significance": str
    }, ...
  ],
  "patient_education": [
    {"number": int, "topic": str}, ...
  ],
  "expected_outcomes": [str, ...]
}

SECTION_KEYS lists the top-level keys that can be independently targeted
during an edit ("metadata" is excluded from editable targeting since it's
housekeeping, but is preserved during merge).
"""

import json
import copy
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gpt-4o"

# Top-level sections of the care plan that can be independently
# identified/edited/merged.
SECTION_KEYS: List[str] = [
    "overview",
    "assessment",
    "diagnoses",
    "medications",
    "lab_findings",
    "patient_education",
    "expected_outcomes",
]

load_dotenv()
_client = None

def _get_client():
    """Create the OpenAI client only when the engine is called."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


# ---------------------------------------------------------------------------
# Shared schema description injected into every LLM call so the model
# always knows the exact shape of the JSON it must produce.
# ---------------------------------------------------------------------------

CARE_PLAN_SCHEMA_DESCRIPTION = """
Return ONLY valid JSON (no markdown fences, no commentary) matching exactly
this structure:

{
  "metadata": {
    "title": "STEM RN CARE PLAN",
    "subtitle": "<Gender> — Chief Complaint / Reason for Admission",
    "nursing_diagnoses_count": <int>,
    "generated_at": "<ISO 8601 timestamp>"
  },
  "overview": {
    "patient_overview": "<narrative paragraph>",
    "disease_overview": "<narrative paragraph>",
    "priority_nursing_diagnoses_summary": [
      {"rank": 1, "title": "<diagnosis label>", "subtitle": "<short r/t phrase>"}
    ]
  },
  "assessment": {
    "subjective_data": ["<string>", ...],
    "objective_data": ["<string>", ...]
  },
  "diagnoses": [
    {
      "diagnosis": "<NANDA-I diagnosis label>",
      "related_to": "<related factors>",
      "as_evidenced_by": ["<string>", ...],
      "smart_goals": [
        {"goal": "<string>", "timeframe": "<string>", "met": false}
      ],
      "nursing_interventions": [
        {"intervention": "<string>", "scientific_rationale": "<string>"}
      ],
      "evaluation_criteria": ["<string>", ...],
      "nclex_pearls": ["<string>", ...]
    }
  ],
  "medications": [
    {"medication": "<string>", "dose": "<string>", "route": "<string>", "nursing_purpose": "<string>"}
  ],
  "lab_findings": [
    {
      "lab_value": "<e.g. CBC (Complete Blood Count)>",
      "patient_value": "<string>",
      "normal_range": "<string>",
      "clinical_significance": "<string>"
    }
  ],
  "patient_education": [
    {"number": 1, "topic": "<string>"}
  ],
  "expected_outcomes": ["<string>", ...]
}

Rules:
- Use evidence-based nursing content aligned with NANDA-I taxonomy and
  current clinical practice guidelines.
- Keep "diagnoses" ordered by clinical priority (Maslow's Hierarchy / ABCs first).
- Do not omit any top-level key, even if a section must be an empty list.
- Do not wrap the JSON in markdown code fences.
"""


# ---------------------------------------------------------------------------
# Low-level helper: call the OpenAI API and parse a JSON object response
# ---------------------------------------------------------------------------

def _call_llm_for_json(system_prompt: str, user_prompt: str,
                        model: str = DEFAULT_MODEL,
                        temperature: float = 0.3) -> Dict[str, Any]:
    """
    Calls the OpenAI chat completions API with JSON-object response mode
    and returns the parsed JSON as a Python dict.

    Raises:
        ValueError: if the model response is not valid JSON.
    """
    response = _get_client().chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_content = response.choices[0].message.content

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM did not return valid JSON. Raw output: {raw_content}"
        ) from exc


# ---------------------------------------------------------------------------
# SCENARIO 1: Generate a brand-new care plan
# ---------------------------------------------------------------------------

def build_generate_prompt(patient_input: Dict[str, Any]) -> str:
    """
    Builds the user-facing prompt sent to the LLM for full care plan
    generation, from the raw "Patient Information" form fields.

    patient_input expected keys (all optional except chief_complaint):
        age, gender, care_setting, chief_complaint, past_medical_history,
        current_medications, allergies, key_vitals, relevant_labs,
        additional_clinical_notes
    """
    fields = {
        "Age": patient_input.get("age", "Not provided"),
        "Gender": patient_input.get("gender", "Not provided"),
        "Care Setting": patient_input.get("care_setting", "Not provided"),
        "Chief Complaint / Reason for Admission": patient_input.get(
            "chief_complaint", "Not provided"
        ),
        "Past Medical History": patient_input.get(
            "past_medical_history", "Not provided"
        ),
        "Current Medications": patient_input.get(
            "current_medications", "Not provided"
        ),
        "Allergies": patient_input.get("allergies", "Not provided"),
        "Key Vitals": patient_input.get("key_vitals", "Not provided"),
        "Relevant Labs / Diagnostics": patient_input.get(
            "relevant_labs", "Not provided"
        ),
        "Additional Clinical Notes": patient_input.get(
            "additional_clinical_notes", "Not provided"
        ),
    }

    field_lines = "\n".join(f"- {label}: {value}" for label, value in fields.items())

    return (
        "Generate a complete nursing care plan for the following patient.\n\n"
        f"{field_lines}\n\n"
        "Produce the full care plan JSON now."
    )


def generate_care_plan(
    patient_input: Dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    SCENARIO 1 entry point.

    Args:
        patient_input: dict of raw "Patient Information" form fields
                        (see build_generate_prompt for expected keys).
        model: OpenAI model name to use.

    Returns:
        A dict matching the full care plan JSON structure, ready to be
        serialized and returned to the frontend / stored by the backend.
    """
    system_prompt = (
        "You are an expert RN care-plan generation assistant used inside a "
        "clinical education tool. You produce structured, evidence-based "
        "nursing care plans.\n\n" + CARE_PLAN_SCHEMA_DESCRIPTION
    )

    user_prompt = build_generate_prompt(patient_input)

    care_plan = _call_llm_for_json(system_prompt, user_prompt, model=model)

    # Ensure generated_at is always accurate/consistent regardless of what
    # the model produced.
    care_plan.setdefault("metadata", {})
    care_plan["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()

    return care_plan


# ---------------------------------------------------------------------------
# SCENARIO 2: Edit an existing care plan
# ---------------------------------------------------------------------------

def identify_affected_sections(
    user_prompt: str,
    existing_care_plan: Dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> List[str]:
    """
    Determines which top-level SECTION_KEYS are relevant to the user's
    requested edit, WITHOUT sending the full care plan content to the LLM
    (only the section names + a short summary of what each contains, and
    the current diagnosis/medication/lab "titles" for grounding).

    Returns:
        A list of section keys (subset of SECTION_KEYS) that must be
        regenerated to satisfy the request. Always contains at least one
        valid section key.
    """
    # Build a lightweight index (titles/labels only) so the model can
    # ground its decision without receiving full section bodies.
    lightweight_index = {
        "overview": "Patient overview, disease overview, priority diagnoses summary",
        "assessment": "Subjective (patient-reported) and objective (nurse-observed) data",
        "diagnoses": [
            d.get("diagnosis") for d in existing_care_plan.get("diagnoses", [])
        ],
        "medications": [
            m.get("medication") for m in existing_care_plan.get("medications", [])
        ],
        "lab_findings": [
            lf.get("lab_value") for lf in existing_care_plan.get("lab_findings", [])
        ],
        "patient_education": [
            pe.get("topic") for pe in existing_care_plan.get("patient_education", [])
        ],
        "expected_outcomes": existing_care_plan.get("expected_outcomes", []),
    }

    system_prompt = (
        "You are a routing assistant for a nursing care-plan editor. Given a "
        "user's edit request and a lightweight index of the current care "
        "plan's sections, decide which top-level sections must be "
        "regenerated to satisfy the request.\n\n"
        f"Valid section keys are exactly: {SECTION_KEYS}\n\n"
        "Respond ONLY with JSON: {\"affected_sections\": [\"<section_key>\", ...]}\n"
        "Include a section only if the user's request requires changing "
        "content that lives in that section. If the request implies a "
        "change to a nursing diagnosis (e.g. adding/removing/altering a "
        "diagnosis, its goals, interventions, or rationale), include "
        "\"diagnoses\" and also \"overview\" (since the priority diagnoses "
        "summary and diagnoses count live there). If unsure, err toward "
        "including a section rather than omitting it."
    )

    user_message = (
        f"User's edit request:\n{user_prompt}\n\n"
        f"Current care plan section index (titles/labels only):\n"
        f"{json.dumps(lightweight_index, indent=2)}\n\n"
        "Which sections must be regenerated?"
    )

    result = _call_llm_for_json(system_prompt, user_message, model=model, temperature=0)

    affected = result.get("affected_sections", [])
    # Defensive filtering: only allow known keys, dedupe, preserve order.
    affected = [s for i, s in enumerate(affected)
                if s in SECTION_KEYS and s not in affected[:i]]

    if not affected:
        # Fallback: if the router failed to identify anything, be safe and
        # do not silently no-op — default to the section most likely to be
        # generically relevant (overview) so the caller still gets *some*
        # sensible update rather than an error.
        affected = ["overview"]

    return affected


def extract_sections(
    existing_care_plan: Dict[str, Any],
    section_keys: List[str],
) -> Dict[str, Any]:
    """
    Extracts only the requested top-level sections from the existing care
    plan. This is the payload that actually gets sent to the LLM for
    editing — the rest of the care plan is never transmitted.
    """
    return {
        key: copy.deepcopy(existing_care_plan.get(key))
        for key in section_keys
        if key in existing_care_plan
    }


def generate_section_updates(
    user_prompt: str,
    sections_subset: Dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Sends ONLY the relevant section(s) of the care plan, along with the
    user's edit request, to the LLM and asks it to return the updated
    versions of exactly those sections.

    Args:
        user_prompt: the user's free-text description of the requested change.
        sections_subset: dict of {section_key: section_content} — output of
                         extract_sections().
        model: OpenAI model name to use.

    Returns:
        A dict containing only the (regenerated) section keys that were
        passed in, e.g. {"diagnoses": [...], "overview": {...}}.
    """
    section_keys = list(sections_subset.keys())

    system_prompt = (
        "You are an expert RN care-plan editing assistant. You will be "
        "given ONLY certain sections of an existing nursing care plan, "
        "plus a user's requested change. Update ONLY the given sections to "
        "reflect the requested change, preserving any content in those "
        "sections that is NOT affected by the request.\n\n"
        f"You MUST return a JSON object with exactly these top-level keys: "
        f"{section_keys}\n\n"
        "Each key's value must follow the same structure as the input for "
        "that key. Do not add extra top-level keys. Do not include any "
        "section not listed above, even if you think it's related — the "
        "caller will only accept the listed keys.\n\n"
        + CARE_PLAN_SCHEMA_DESCRIPTION
    )

    user_message = (
        f"User's requested change:\n{user_prompt}\n\n"
        f"Current content of the section(s) to edit:\n"
        f"{json.dumps(sections_subset, indent=2)}\n\n"
        "Return the updated JSON for exactly these section(s)."
    )

    updated_sections = _call_llm_for_json(system_prompt, user_message, model=model)

    # Defensive: only keep keys we actually asked for.
    return {k: v for k, v in updated_sections.items() if k in section_keys}


def merge_care_plan(
    original_care_plan: Dict[str, Any],
    updated_sections: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merges regenerated section(s) back into the original care plan,
    leaving every other section untouched. Also refreshes metadata
    (generated_at, nursing_diagnoses_count) to stay consistent.

    Returns:
        The complete, updated care plan dict.
    """
    merged = copy.deepcopy(original_care_plan)

    for key, value in updated_sections.items():
        merged[key] = value

    merged.setdefault("metadata", {})
    merged["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
    if "diagnoses" in merged:
        merged["metadata"]["nursing_diagnoses_count"] = len(merged["diagnoses"])

    return merged


def edit_care_plan(
    user_prompt: str,
    existing_care_plan: Dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    SCENARIO 2 entry point (orchestrator).

    Args:
        user_prompt: the user's free-text description of the requested edit.
        existing_care_plan: the full, previously generated care plan dict.
        model: OpenAI model name to use for all sub-calls.

    Returns:
        The complete, updated care plan dict (all unaffected sections
        preserved verbatim from existing_care_plan).
    """
    affected_sections = identify_affected_sections(
        user_prompt, existing_care_plan, model=model
    )

    sections_subset = extract_sections(existing_care_plan, affected_sections)

    updated_sections = generate_section_updates(
        user_prompt, sections_subset, model=model
    )

    return merge_care_plan(existing_care_plan, updated_sections)
