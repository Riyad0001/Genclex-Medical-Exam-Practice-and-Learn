import os
import json
import re
import base64
import io
from typing import List, Optional, Union, Dict, Any

from django.conf import settings
from openai import OpenAI

try:
    import json_repair
except ImportError:
    json_repair = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

from pydantic import BaseModel, Field, model_validator


# Static onboarding greeting
CARA_WELCOME_MESSAGE = """Hi, I'm CARA. Tell me about your patient or upload a clinical file/chart image, and I'll build a comprehensive concept map.

I work with single illnesses or complex patient cases — the more detail provided, the richer the map. Include whatever you have:

**Patient Profile** – age, gender, reason for admission / chief complaint
**Medical History** – primary dx, comorbidities (e.g., DM + HTN + CKD), surgical hx
**Pathophysiology** – disease mechanisms and underlying physiologic processes
**Subjective Data** – what the patient reports (pain 7/10, anxiety, SOB, nausea)
**Objective Data** – physical assessment findings (lung sounds, skin, edema)
**Vital Signs** – BP, HR, RR, SpO2, Temperature with actual values
**Laboratory & Diagnostics** – BNP, Creatinine, Electrolytes, ECG, Chest X-Ray
**Medications** – current meds, dosages, indications, and safety monitoring
**Nursing Diagnoses & Interventions** – NANDA problems, actions, and safety precautions
**Monitoring & Expected Outcomes** – reassessments, goals, and complication prevention

Quick start example:
"72F admitted for CHF exacerbation. Hx: HTN, T2DM, CKD stage 3. c/o SOB and fatigue. BP 158/92, HR 104, SpO2 89% RA, crackles bilaterally, 2+ pitting edema. BNP 980, Cr 2.1. On Lasix 40mg IV, metoprolol, lisinopril, metformin. Currently on 2L O2 NC, daily weights, fluid restriction." """


def get_welcome_message() -> str:
    return CARA_WELCOME_MESSAGE


# ---------------------------------------------------------------------------
# Standard Allowed Node Categories
VALID_CATEGORIES = {
    "Central",
    "Pathophysiology",
    "Risk Factor",
    "Subjective Data",
    "Objective Data",
    "Vital Sign",
    "Laboratory",
    "Diagnostic",
    "Nursing Diagnosis",
    "Intervention",
    "Medication",
    "Monitoring",
    "Complication",
    "Expected Outcome",
    "Patient Education",
    "Safety",
}


class ConceptNode(BaseModel):
    id: str = Field(description="Unique node identifier, e.g., 'n_central', 'n_dx_fluid'")
    label: str = Field(description="Title or concept name, e.g., 'Excess Fluid Volume'")
    details: str = Field(default="", description="Concise clinical notes, rationale, or explanation")
    category: str = Field(
        default="Intervention",
        description="Must be one of the 16 standard category strings",
    )
    priority: Optional[str] = Field(default="medium", description="high | medium | low")
    patientSpecific: Optional[bool] = Field(default=True, description="True if patient specific")
    bgColor: Optional[str] = Field(default=None, description="Custom background fill hex color e.g. #EEF4FA")
    textColor: Optional[str] = Field(default=None, description="Custom text font hex color e.g. #0F172A")

    @model_validator(mode="before")
    @classmethod
    def normalize_node(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "label" not in data and "title" in data:
                data["label"] = data["title"]
            if "label" not in data and "name" in data:
                data["label"] = data["name"]
            if "id" not in data and "label" in data:
                data["id"] = "n_" + re.sub(r"\W+", "_", str(data["label"])).lower()[:25]

            cat = str(data.get("category", "")).strip()
            cat_lower = cat.lower()

            if "central" in cat_lower or "primary" in cat_lower or "chief" in cat_lower:
                data["category"] = "Central"
            elif "patho" in cat_lower or "mechanism" in cat_lower:
                data["category"] = "Pathophysiology"
            elif "risk" in cat_lower or "history" in cat_lower or "comorbid" in cat_lower:
                data["category"] = "Risk Factor"
            elif "subjective" in cat_lower or "symptom" in cat_lower or "reported" in cat_lower:
                data["category"] = "Subjective Data"
            elif "vital" in cat_lower or "bp" in cat_lower or "spo2" in cat_lower or "pulse" in cat_lower or "temp" in cat_lower:
                data["category"] = "Vital Sign"
            elif "lab" in cat_lower or "blood" in cat_lower or "bnp" in cat_lower or "creatinine" in cat_lower or "k+" in cat_lower:
                data["category"] = "Laboratory"
            elif "diagnostic" in cat_lower or "x-ray" in cat_lower or "echo" in cat_lower or "ecg" in cat_lower or "ct" in cat_lower or "scan" in cat_lower:
                data["category"] = "Diagnostic"
            elif "objective" in cat_lower or "exam" in cat_lower or "finding" in cat_lower:
                data["category"] = "Objective Data"
            elif "diagnosis" in cat_lower or "nanda" in cat_lower or "dx" in cat_lower:
                data["category"] = "Nursing Diagnosis"
            elif "intervent" in cat_lower or "action" in cat_lower or "care plan" in cat_lower:
                data["category"] = "Intervention"
            elif "med" in cat_lower or "pharm" in cat_lower or "drug" in cat_lower or "treatment" in cat_lower:
                data["category"] = "Medication"
            elif "monitor" in cat_lower or "reassess" in cat_lower or "i&o" in cat_lower:
                data["category"] = "Monitoring"
            elif "complication" in cat_lower or "emergency" in cat_lower or "deterioration" in cat_lower:
                data["category"] = "Complication"
            elif "outcome" in cat_lower or "goal" in cat_lower:
                data["category"] = "Expected Outcome"
            elif "education" in cat_lower or "teaching" in cat_lower or "instruction" in cat_lower:
                data["category"] = "Patient Education"
            elif "safety" in cat_lower or "precaution" in cat_lower or "fall" in cat_lower:
                data["category"] = "Safety"
            else:
                matched = False
                for valid_cat in VALID_CATEGORIES:
                    if valid_cat.lower() == cat_lower:
                        data["category"] = valid_cat
                        matched = True
                        break
                if not matched:
                    data["category"] = "Intervention"

            # Clean and ensure non-empty details
            raw_details = str(data.get("details") or "").strip()
            if not raw_details or raw_details in [".", "-", "null", "None"]:
                label_text = data.get("label", "Clinical Finding")
                data["details"] = f"Clinical rationale, monitoring requirements, and nursing management related to {label_text}."
            else:
                data["details"] = raw_details

        return data


class ConceptEdge(BaseModel):
    id: str = Field(default="", description="Internal-only unique edge id")
    source: str = Field(default="", description="ID of the parent/source node")
    target: str = Field(default="", description="ID of the child/target node")
    label: Optional[str] = Field(None, description="Relationship description")
    priority: Optional[str] = Field(default="medium", description="high | medium | low")

    @model_validator(mode="before")
    @classmethod
    def normalize_edge(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "source" not in data and "from" in data:
                data["source"] = data.get("from", "")
            if "target" not in data and "to" in data:
                data["target"] = data.get("to", "")
            if not data.get("id"):
                data["id"] = f"e_{data.get('source', 'src')}_{data.get('target', 'tgt')}"
        return data


class ConceptMap(BaseModel):
    title: str = Field(default="Clinical Concept Map")
    nodes: List[ConceptNode] = Field(default_factory=list)
    edges: List[ConceptEdge] = Field(default_factory=list)


_SYSTEM_PROMPT = """SYSTEM PROMPT — CARA CLINICAL REASONING CONCEPT MAP ENGINE

You are CARA, an expert Clinical Nursing Educator AI specializing in patient-specific clinical reasoning and interconnected nursing concept maps.

Your task is to build, edit, or extend a concept map that helps nursing students understand HOW all patient data connects.

The concept map must not merely sort information into categories.

It must show clinically meaningful relationships among:

- Primary medical condition
- Pathophysiology
- Comorbidities and risk factors
- Subjective symptoms
- Objective assessment findings
- Vital signs
- Laboratory results
- Diagnostic results
- Medications
- Nursing diagnoses
- Nursing interventions
- Monitoring parameters
- Complications
- Safety concerns
- Patient education
- Expected outcomes

The map must allow the student to visually trace:

DISEASE
→ PATHOPHYSIOLOGY
→ PATIENT FINDINGS
→ VITALS / LABS / DIAGNOSTICS
→ NURSING PROBLEMS
→ MEDICATIONS / INTERVENTIONS
→ MONITORING
→ OUTCOMES / COMPLICATIONS

==================================================
CRITICAL QUALITY REQUIREMENTS
==================================================

1. EVERY node MUST contain a meaningful, non-empty `details` string.

2. `details` should contain 1–3 concise clinical sentences explaining:
   - why the finding matters,
   - how it relates to this patient,
   - or what the nurse should understand from it.

3. NEVER use empty, null, placeholder, or meaningless details.

4. DO NOT simply connect every node to the Central node.

5. Prefer causal and clinically meaningful chains.

6. Cross-category relationships are REQUIRED whenever clinically relevant.

7. Do not create unnecessary connections simply because a theoretical relationship exists.

8. Use patient-specific data whenever available.

9. Never fabricate patient-specific numeric values that were not provided.

10. Physiologic mechanisms may be added when needed to explain an evidence-supported relationship.

==================================================
ALLOWED NODE CATEGORIES
==================================================

Every node MUST use EXACTLY one of these category strings:

- "Central"
- "Pathophysiology"
- "Risk Factor"
- "Subjective Data"
- "Objective Data"
- "Vital Sign"
- "Laboratory"
- "Diagnostic"
- "Nursing Diagnosis"
- "Intervention"
- "Medication"
- "Monitoring"
- "Complication"
- "Expected Outcome"
- "Patient Education"
- "Safety"

==================================================
NODE DEFINITIONS
==================================================

1. "Central"

Exactly ONE primary central node.

Represents the main reason for admission or highest-level medical problem.

Example:
label: "Acute Decompensated Heart Failure"

details:
"72-year-old patient admitted with volume-overloaded heart failure, dyspnea, hypoxemia, and worsening renal function."

Do NOT combine every comorbidity into the Central label.

Comorbidities should generally remain separate nodes so they can connect to relevant pathways.

--------------------------------------------------

2. "Pathophysiology"

Represents the physiologic mechanisms connecting disease to patient findings.

Examples:

"Decreased LV Contractility"
"Reduced Cardiac Output"
"RAAS Activation"
"Sodium and Water Retention"
"Pulmonary Congestion"
"Impaired Gas Exchange"

Use these nodes to show WHY the patient's findings are occurring.

Pathophysiology nodes may be added even if the exact phrase was not supplied by the user when the mechanism is clinically established and necessary to explain the provided data.

Do NOT add speculative pathophysiology.

--------------------------------------------------

3. "Risk Factor"

Includes:

- Chronic comorbidities
- Relevant past medical history
- Lifestyle risks
- Age-related risks
- Family history
- Predisposing factors

Examples:

"Hypertension"
"Type 2 Diabetes"
"CKD Stage 3"
"Smoking History"

Risk factors and comorbidities must connect to the specific disease process, lab, medication, or complication they influence.

Do NOT automatically connect every Risk Factor only to Central.

--------------------------------------------------

4. "Subjective Data"

Patient-reported information.

Examples:

"Shortness of Breath"
"Fatigue"
"Orthopnea"
"Pain 7/10"
"Nausea"

Subjective data should connect to the physiologic problem or nursing diagnosis it supports.

Do NOT automatically connect all subjective data directly to Central.

--------------------------------------------------

5. "Objective Data"

Physical assessment findings that are observed or measured but are NOT vital signs, labs, or diagnostic tests.

Examples:

"Crackles Bilaterally"
"2+ Pitting Edema"
"Cool Extremities"
"Distended Abdomen"
"Confusion"

Objective findings should connect to their likely underlying physiologic cause and/or nursing diagnosis.

--------------------------------------------------

6. "Vital Sign"

Use for:

- Blood pressure
- Heart rate
- Respiratory rate
- Temperature
- SpO2

Always preserve the patient's actual value when provided.

Examples:

"SpO₂ 89% on Room Air"
"BP 158/92"
"HR 104 bpm"

Each abnormal vital sign must connect to its likely significance.

Also connect to relevant medications, interventions, or monitoring when appropriate.

--------------------------------------------------

7. "Laboratory"

Use for specific laboratory values.

Examples:

"BNP 980 pg/mL"
"Creatinine 2.1 mg/dL"
"K⁺ 4.8 mEq/L"
"Na⁺ 134 mEq/L"

For each significant lab determine:

- What might explain it?
- What disease does it support?
- Does it indicate severity?
- Does it affect medication safety?
- Does it require monitoring?
- Does it increase complication risk?

Laboratory nodes should frequently have more than one clinically meaningful connection.

--------------------------------------------------

8. "Diagnostic"

Use for diagnostic studies and imaging.

Examples:

"Chest X-ray: Pulmonary Congestion"
"Echocardiogram: EF 35%"
"ECG: Atrial Fibrillation"
"CT: Pulmonary Embolism"

Connect diagnostic findings to the condition or physiologic process they support.

--------------------------------------------------

9. "Nursing Diagnosis"

Use recognized nursing-diagnosis terminology where appropriate.

The diagnosis must be supported by patient-specific evidence.

Example:

label:
"Impaired Gas Exchange"

details:
"Related to pulmonary congestion as evidenced by SpO₂ 89% on room air, dyspnea, tachypnea, and bilateral crackles."

Do NOT require every nursing diagnosis to connect directly from Central.

Preferred structure:

Patient finding / physiologic problem
→ supports
→ Nursing Diagnosis

Examples:

"Pulmonary Congestion"
→ contributes to
→ "Impaired Gas Exchange"

"SpO₂ 89%"
→ evidenced by
→ "Impaired Gas Exchange"

--------------------------------------------------

10. "Intervention"

Represents nursing or provider-directed care.

Examples:

"Oxygen 2 L NC"
"Daily Weights"
"Strict Intake and Output"
"Fluid Restriction"
"Low-Sodium Diet"
"Elevate HOB"

Interventions should connect to the problem they address.

Examples:

"Impaired Gas Exchange"
→ managed by
→ "Oxygen 2 L NC"

"Fluid Volume Excess"
→ managed by
→ "Daily Weights"

Do NOT require every Intervention to connect only from a Nursing Diagnosis.

An intervention may also connect directly to:

- a vital sign,
- a physiologic problem,
- a complication risk,
- or a monitoring need.

--------------------------------------------------

11. "Medication"

Each medication must be clinically integrated.

For EACH medication determine:

A. What condition or physiologic problem does it treat?

B. What physiologic effect does it produce?

C. What patient findings should improve?

D. Which labs must be monitored?

E. Which vital signs must be monitored?

F. Which comorbidities change its safety profile?

G. Which adverse effects are especially relevant to this patient?

H. Does it interact clinically with another medication?

Medication nodes must NOT automatically connect only to Central.

Examples:

"Furosemide"
→ treats
→ "Fluid Volume Overload"

"Furosemide"
→ requires monitoring of
→ "K⁺"

"Furosemide"
→ requires monitoring of
→ "Creatinine"

"Furosemide"
→ expected to improve
→ "Peripheral Edema"

"Metoprolol"
→ decreases
→ "Heart Rate"

"Lisinopril"
→ requires monitoring of
→ "Creatinine"

"Lisinopril"
→ requires monitoring of
→ "K⁺"

--------------------------------------------------

12. "Monitoring"

Use when the nurse must repeatedly reassess something.

Examples:

"Daily Weight"
"Strict I&O"
"Repeat BMP"
"Monitor BP/HR"
"Assess Lung Sounds"
"Monitor Urine Output"

Monitoring must connect to WHY it is necessary.

Examples:

"Furosemide"
→ requires monitoring of
→ "Potassium"

"Fluid Overload"
→ monitored by
→ "Daily Weight"

"CKD"
→ requires monitoring of
→ "Renal Function"

--------------------------------------------------

13. "Complication"

Represents realistic patient-specific deterioration or adverse outcomes.

Examples:

"Pulmonary Edema"
"Acute Kidney Injury"
"Dysrhythmia"
"Shock"
"Sepsis"

Complication nodes should connect to the pathway producing the risk.

Do NOT add complications merely because they are theoretically possible.

--------------------------------------------------

14. "Expected Outcome"

Represents measurable improvement or stabilization.

Examples:

"SpO₂ ≥94%"
"Reduced Dyspnea"
"Decreased Edema"
"Stable Creatinine"
"Improved Urine Output"

Expected outcomes should connect to the intervention, medication, or problem being treated.

--------------------------------------------------

15. "Patient Education"

Use for meaningful patient teaching.

Examples:

"Daily Home Weights"
"Low-Sodium Diet"
"Medication Adherence"
"Signs of Worsening Heart Failure"
"Glucose Monitoring"

Patient education should connect to the disease, medication, or complication it is intended to manage or prevent.

--------------------------------------------------

16. "Safety"

Use for immediate nursing safety considerations.

Examples:

"Fall Precautions"
"Bleeding Precautions"
"Aspiration Precautions"
"Seizure Precautions"
"Orthostatic Safety"

Connect safety precautions to the medication, condition, or assessment finding that creates the risk.

==================================================
CLINICAL RELATIONSHIP ENGINE
==================================================

Before creating edges, internally evaluate the patient data as a clinical reasoning graph.

Use:

SOURCE → RELATIONSHIP → TARGET

For EVERY clinically important node, ask:

1. What causes this?
2. What does this cause?
3. What supports this?
4. What does this worsen?
5. What treats this?
6. What should improve because of treatment?
7. What must be monitored because of this?
8. What lab affects this?
9. What vital sign affects this?
10. What medication affects this?
11. What comorbidity affects this?
12. What complication may follow this?

==================================================
VALID EDGE RELATIONSHIPS
==================================================

Use concise, meaningful labels such as:

"causes"
"contributes to"
"leads to"
"results in"
"activates"
"increases"
"decreases"
"worsens"
"improves"
"supports"
"evidenced by"
"associated with"
"treated with"
"treats"
"managed by"
"monitored by"
"requires monitoring of"
"expected to improve"
"increases risk of"
"may progress to"
"reduces"
"prevents"
"affects"
"secondary to"

Edge labels are NOT restricted to category-specific values.

Choose the clinically most accurate relationship.

==================================================
IMPORTANT CROSS-CONNECTION RULES
==================================================

Cross-category connections are REQUIRED when clinically meaningful.

Examples:

Risk Factor → Pathophysiology
Risk Factor → Laboratory
Risk Factor → Medication
Risk Factor → Complication
Pathophysiology → Objective Data
Pathophysiology → Vital Sign
Pathophysiology → Laboratory
Pathophysiology → Nursing Diagnosis
Vital Sign → Nursing Diagnosis
Vital Sign → Intervention
Vital Sign → Medication
Laboratory → Medication
Laboratory → Complication
Laboratory → Monitoring
Medication → Laboratory
Medication → Vital Sign
Medication → Monitoring
Medication → Objective Data
Medication → Expected Outcome
Nursing Diagnosis → Intervention
Intervention → Monitoring
Intervention → Expected Outcome
Complication → Monitoring
Patient Education → Complication Prevention
Safety → Intervention

==================================================
ANTI-HUB-AND-SPOKE RULE
==================================================

The Central node is NOT the required source or destination for most edges.

The map should not visually resemble:
Everything → Central → Everything.

Instead it should resemble interconnected clinical pathways.
Use the Central node only where clinically appropriate.
Whenever a more specific pathophysiologic, assessment, lab, medication, or nursing connection exists, prefer that specific relationship.

==================================================
ANTI-SPAGHETTI RULE
==================================================

Do not connect everything to everything.
Only create an edge if the relationship is clinically meaningful.

==================================================
PATIENT-SPECIFIC REASONING
==================================================

Always prioritize the patient's ACTUAL supplied data.
Do not invent missing numeric data.

==================================================
STATE SENSITIVITY
==================================================

The [CURRENT CONCEPT MAP STATE] block is the source of truth for existing nodes and edges unless the user specifically requests changes.

When editing:
- Preserve existing node IDs whenever the same concept remains.
- Preserve unaffected nodes and edges.
- Add new nodes using unique IDs.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY one valid JSON object.

Format:

{
  "title": "string",
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "details": "string",
      "category": "string",
      "priority": "high|medium|low",
      "patientSpecific": true
    }
  ],
  "edges": [
    {
      "source": "node_id",
      "target": "node_id",
      "label": "string",
      "priority": "high|medium|low"
    }
  ]
}

No markdown. No commentary. No explanation outside the JSON.
"""


def extract_file_content(uploaded_file) -> Dict[str, Any]:
    """
    Extracts text content or image base64 payload from an uploaded Django file object.
    Returns dict with keys: 'text': str, 'image_url': Optional[str], 'file_name': str
    """
    file_name = uploaded_file.name
    content_type = getattr(uploaded_file, "content_type", "") or ""
    ext = os.path.splitext(file_name)[1].lower()

    # Read bytes
    file_bytes = uploaded_file.read()

    # 1. Image Files (PNG, JPG, JPEG, WEBP)
    if ext in [".png", ".jpg", ".jpeg", ".webp"] or "image" in content_type:
        mime = content_type if "image" in content_type else f"image/{ext.replace('.', '')}"
        if ext == ".jpg":
            mime = "image/jpeg"
        b64_str = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "text": f"[Uploaded Image File: {file_name}]",
            "image_url": f"data:{mime};base64,{b64_str}",
            "file_name": file_name,
        }

    # 2. PDF Files
    if ext == ".pdf" or "pdf" in content_type:
        extracted_text = ""
        if PyPDF2:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        extracted_text += t + "\n"
            except Exception as e:
                extracted_text = f"[Error reading PDF pages: {e}]"
        else:
            extracted_text = "[PyPDF2 not installed on server]"

        return {
            "text": extracted_text.strip() or f"[PDF File: {file_name} — no readable text extracted]",
            "image_url": None,
            "file_name": file_name,
        }

    # 3. DOCX Files
    if ext in [".docx", ".doc"]:
        extracted_text = ""
        if docx and ext == ".docx":
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                paragraphs = [p.text for p in doc.paragraphs if p.text]
                extracted_text = "\n".join(paragraphs)
            except Exception as e:
                extracted_text = f"[Error reading DOCX file: {e}]"
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")

        return {
            "text": extracted_text.strip() or f"[Word Document: {file_name}]",
            "image_url": None,
            "file_name": file_name,
        }

    # 4. Text-based files (TXT, CSV, MD, JSON, HTML, LOG, RTF)
    try:
        text_content = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text_content = f"[Binary File: {file_name}]"

    return {
        "text": text_content.strip(),
        "image_url": None,
        "file_name": file_name,
    }


def _strip_to_schema_fields(current_state: dict) -> dict:
    """Keep only fields the AI should read/edit, dropping DB-only bookkeeping fields."""
    nodes = []
    for n in current_state.get("nodes", []) or []:
        if not isinstance(n, dict):
            continue
        nodes.append({
            "id": n.get("id"),
            "label": n.get("label") or n.get("title") or n.get("name"),
            "details": n.get("details"),
            "category": n.get("category"),
            "priority": n.get("priority", "medium"),
            "patientSpecific": n.get("patientSpecific", True),
            "bgColor": n.get("bgColor"),
            "textColor": n.get("textColor"),
        })

    edges = []
    for e in current_state.get("edges", []) or []:
        if not isinstance(e, dict):
            continue
        edges.append({
            "source": e.get("source") or e.get("from"),
            "target": e.get("target") or e.get("to"),
            "label": e.get("label"),
            "priority": e.get("priority", "medium"),
        })

    return {
        "title": current_state.get("title", "Clinical Concept Map"),
        "nodes": nodes,
        "edges": edges,
    }


def _drop_dangling_edges(concept_map: dict) -> dict:
    valid_ids = {n["id"] for n in concept_map.get("nodes", [])}
    concept_map["edges"] = [
        e for e in concept_map.get("edges", [])
        if e.get("source") in valid_ids and e.get("target") in valid_ids
    ]
    return concept_map


def update_nursing_concept_map(
    user_prompt: str,
    current_concept_map: Optional[dict] = None,
    uploaded_file=None,
) -> dict:
    """
    Given a user prompt, optional uploaded file, and optional current map state,
    calls OpenAI API and returns the full concept map dictionary.
    """
    is_new_map = not current_concept_map or not current_concept_map.get("nodes")
    current_state = current_concept_map or {"title": "New Concept Map", "nodes": [], "edges": []}

    content_only_state = _strip_to_schema_fields(current_state)

    # Ensure environment variables from .env are refreshed
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(settings.BASE_DIR, ".env"), override=True)
    except Exception:
        pass

    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment or Django settings.")

    client = OpenAI(api_key=api_key)

    # Process file upload if provided
    file_info = None
    if uploaded_file:
        file_info = extract_file_content(uploaded_file)

    action_note = (
        "This is a NEW concept map — build it from scratch based on the user request and clinical data."
        if is_new_map
        else "This is an EDIT to an EXISTING concept map — preserve all unchanged nodes/edges exactly as-is, "
             "apply only the requested change(s), and return the full resulting map."
    )

    combined_text = user_prompt.strip()
    if file_info and file_info.get("text"):
        combined_text = f"=== UPLOADED CLINICAL FILE ({file_info['file_name']}) ===\n{file_info['text']}\n\n=== USER INSTRUCTIONS / CASE NOTES ===\n{combined_text}"

    if not combined_text and file_info and file_info.get("image_url"):
        combined_text = f"Analyze the uploaded patient clinical chart image ({file_info['file_name']}) and build a concept map."

    # Construct user message content (multimodal if image is present)
    if file_info and file_info.get("image_url"):
        user_message_payload = [
            {
                "type": "text",
                "text": f"""[CURRENT CONCEPT MAP STATE]:
{json.dumps(content_only_state, indent=2)}

[CLINICAL DATA / REQUEST]:
{combined_text}

[NOTE]: {action_note}

Provide response strictly in valid JSON format matching the schema. Return the complete map (all nodes and edges)."""
            },
            {
                "type": "image_url",
                "image_url": {"url": file_info["image_url"]}
            }
        ]
    else:
        user_message_payload = f"""[CURRENT CONCEPT MAP STATE]:
{json.dumps(content_only_state, indent=2)}

[CLINICAL DATA / REQUEST]:
{combined_text}

[NOTE]: {action_note}

Provide response strictly in valid JSON format matching the schema. Return the complete map (all nodes and edges)."""

    model_name = os.getenv("CONCEPT_MAP_OPENAI_MODEL", "gpt-4o")

    response = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message_payload},
        ],
    )

    response_text = (response.choices[0].message.content or "").strip()

    if not response_text:
        raise ValueError("OpenAI API response contained no text content to parse as JSON.")

    try:
        parsed_json = json.loads(response_text)
    except json.JSONDecodeError:
        if json_repair is not None:
            parsed_json = json_repair.loads(response_text)
        else:
            raise

    validated_map = ConceptMap.model_validate(parsed_json).model_dump()
    final_map = _drop_dangling_edges(validated_map)

    # Sanitize any null bytes or invalid control characters
    for node in final_map.get("nodes", []):
        for k, v in list(node.items()):
            if isinstance(v, str):
                node[k] = v.replace("\x00", "").replace("\u0000", "")

    for edge in final_map.get("edges", []):
        for k, v in list(edge.items()):
            if isinstance(v, str):
                edge[k] = v.replace("\x00", "").replace("\u0000", "")

    return final_map
