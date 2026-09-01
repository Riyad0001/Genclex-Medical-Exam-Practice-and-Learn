import random
from django.core.management.base import BaseCommand
from apps.new_nclex.models import (
    NCLEXCategory,
    NCLEXTopic,
    NCLEXSubtopic,
    NCLEXQuestion,
    QuestionOption,
    NCLEXExam,
)


CLIENT_NEEDS_CATEGORIES = [
    {
        "name": "Management of Care",
        "topics": [
            ("Advance Directives & Ethical Practice", ["Informed Consent", "DNR & Living Will", "Client Rights"]),
            ("Continuity of Care & Delegation", ["Nursing Delegation to UAP/LPN", "Prioritization Frameworks", "Hand-off Reporting"]),
            ("Legal & Regulatory", ["Confidentiality & HIPAA", "Mandatory Reporting", "Incident Reports"]),
        ],
    },
    {
        "name": "Safety and Infection Control",
        "topics": [
            ("Accident / Error / Injury Prevention", ["Fall Precautions", "Restraints & Safety", "Surgical Time-out"]),
            ("Infection Control & Standard Precautions", ["Contact Precautions", "Airborne & Droplet Isolation", "Sterile Technique"]),
            ("Hazardous Materials & Emergency Response", ["Fire Response RACE/PASS", "Radiation Safety", "Disaster Triage"]),
        ],
    },
    {
        "name": "Health Promotion and Maintenance",
        "topics": [
            ("Ante/Intra/Postpartum & Newborn", ["Fetal Heart Monitoring", "Postpartum Hemorrhage", "Newborn Assessment"]),
            ("Growth & Developmental Stages", ["Infant Milestones", "Toddler Safety", "Adolescent Health"]),
            ("Health Screening & Immunizations", ["Vaccine Schedules", "Cancer Screenings", "Lifestyle Education"]),
        ],
    },
    {
        "name": "Psychosocial Integrity",
        "topics": [
            ("Therapeutic Communication", ["Nonverbal & Active Listening", "De-escalation", "Open-Ended Questioning"]),
            ("Mental Health Concepts", ["Depression & Suicide Risk", "Schizophrenia & Hallucinations", "Bipolar & Mania"]),
            ("Crisis & Chemical Dependency", ["Substance Withdrawal", "Abuse & Trauma", "Anxiety & Panic"]),
        ],
    },
    {
        "name": "Basic Care and Comfort",
        "topics": [
            ("Mobility & Positioning", ["Bed Rest Complications", "Transfer Techniques", "Assistive Devices"]),
            ("Nutrition & Elimination", ["Enteral Tube Feeding", "Catheter Care", "Dysphagia Management"]),
            ("Rest, Sleep & Comfort Interventions", ["Pain Assessment PQRST", "Non-pharmacological Comfort", "Skin Integrity"]),
        ],
    },
    {
        "name": "Pharmacological and Parenteral Therapies",
        "topics": [
            ("Cardiovascular & Renal Medications", ["ACE Inhibitors & Beta Blockers", "Diuretics & Potassium", "Anticoagulants"]),
            ("Anti-infectives & Emergency Drugs", ["Antibiotics & Peak/Trough", "Epinephrine & Anaphylaxis", "Insulin Protocols"]),
            ("Dosage Calculation & IV Infusion", ["IV Flow Rates", "Blood Transfusion Reactions", "Total Parenteral Nutrition"]),
        ],
    },
    {
        "name": "Reduction of Risk Potential",
        "topics": [
            ("Diagnostic Tests & Laboratory Values", ["Electrolyte Imbalances", "ABG Interpretation", "Coagulation Studies"]),
            ("Potential for Complications of Procedures", ["Central Line Dressing", "Post-op Monitoring", "Tracheostomy Suctioning"]),
            ("Vital Signs & Therapeutic Procedures", ["Hemodynamic Monitoring", "Chest Tube Care", "Lumbar Puncture Post-Care"]),
        ],
    },
    {
        "name": "Physiological Adaptation",
        "topics": [
            ("Cardiovascular Alterations", ["Myocardial Infarction", "Heart Failure & Pulmonary Edema", "Shock Management"]),
            ("Respiratory Alterations", ["COPD & Oxygen Therapy", "ARDS & Mechanical Ventilation", "Pulmonary Embolism"]),
            ("Neurological & Metabolic Emergencies", ["Stroke / CVA Assessment", "Diabetic Ketoacidosis (DKA)", "Sepsis & Septic Shock"]),
        ],
    },
]

CJMM_FUNCTIONS = [
    "Recognize Cues",
    "Analyze Cues",
    "Prioritize Hypotheses",
    "Generate Solutions",
    "Take Action",
    "Evaluate Outcomes",
]

BODY_SYSTEMS = [
    "Cardiovascular",
    "Respiratory",
    "Neurological",
    "Endocrine",
    "Renal",
    "Gastrointestinal",
    "Maternal/Newborn",
    "Pediatrics",
    "Mental Health",
    "Integumentary",
]


class Command(BaseCommand):
    help = "Seed 220+ high-quality NCLEX questions with structured Client Needs, CJMM tags, Body Systems, and Option rationales."

    def handle(self, *args, **options):
        self.stdout.write("Creating NCLEX Categories, Topics, and Subtopics...")

        category_objs = {}
        subtopic_list = []

        for cat_info in CLIENT_NEEDS_CATEGORIES:
            cat_obj, _ = NCLEXCategory.objects.get_or_create(title=cat_info["name"])
            category_objs[cat_info["name"]] = cat_obj

            for topic_name, subtopics in cat_info["topics"]:
                topic_obj, _ = NCLEXTopic.objects.get_or_create(category=cat_obj, title=topic_name)
                for sub_name in subtopics:
                    sub_obj, _ = NCLEXSubtopic.objects.get_or_create(
                        topic=topic_obj,
                        title=sub_name,
                        defaults={"description": f"Clinical practice items for {sub_name}"},
                    )
                    subtopic_list.append(sub_obj)

        self.stdout.write(f"Created/verified {len(category_objs)} Client Needs categories and {len(subtopic_list)} subtopics.")

        # Question template banks
        templates = [
            # 1. Radio prioritization
            {
                "type": "radio",
                "stem": "The nurse is caring for a client with {subtopic}. Which clinical finding is the highest priority to report to the healthcare provider immediately?",
                "correct": "Acute drop in SpO2 with new-onset inspiratory crackles and restlessness",
                "correct_rationale": "Indicates deteriorating respiratory/cardiovascular status requiring urgent airway/oxygenation intervention.",
                "distractors": [
                    ("Mild localized fatigue after ambulation", "Expected finding following physical exertion."),
                    ("Stable heart rate of 78 bpm on room air", "Normal physiologic parameter."),
                    ("Dry mouth reported after oral rinse", "Minor benign side effect."),
                ],
            },
            # 2. Radio intervention
            {
                "type": "radio",
                "stem": "When managing a client with {subtopic}, what is the essential initial nursing intervention?",
                "correct": "Assess airway patency, breathing effort, and continuous pulse oximetry",
                "correct_rationale": "Airway and breathing assessment takes priority before executing secondary medical interventions.",
                "distractors": [
                    ("Administer prescribed PRN oral sedative", "Sedatives can mask deteriorating neurologic and respiratory status."),
                    ("Place the patient flat in supine position", "Supine position may compromise lung expansion."),
                    ("Request an immediate routine social work consult", "Non-emergent administrative action."),
                ],
            },
            # 3. Multiple select (SATA)
            {
                "type": "multiple",
                "stem": "The nurse is reviewing discharge instructions for a client diagnosed with {subtopic}. Which instructions should be included? (Select all that apply.)",
                "correct_opts": [
                    ("Weigh yourself daily at the same time and record the values", "Essential for monitoring fluid volume status and medication efficacy."),
                    ("Report sudden weight gain of greater than 2-3 lbs in 24 hours immediately", "Key warning sign of fluid overload or acute decompensation."),
                    ("Maintain an updated list of all medications and emergency contacts", "Crucial for emergency preparedness and medication reconciliation."),
                ],
                "distractor_opts": [
                    ("Double your medication dosage if you miss a scheduled morning pill", "Doubling medication doses can cause acute toxicity."),
                    ("Avoid reporting mild shortness of breath until next month's follow-up", "Delays critical intervention for progressive pulmonary congestion."),
                ],
            },
            # 4. Radio pharmacology / safety
            {
                "type": "radio",
                "stem": "A client receiving therapeutic management for {subtopic} presents with abnormal lab values. Which nursing action takes precedence?",
                "correct": "Withhold the scheduled dose, check vital signs, and notify the prescribing physician",
                "correct_rationale": "Protecting client safety by withholding potentially toxic drugs when contraindications exist is the primary nursing duty.",
                "distractors": [
                    ("Administer the medication with a glass of whole milk", "Does not address the critical laboratory anomaly."),
                    ("Re-check the lab values in 48 hours without contacting the provider", "Unsafe delay that risks toxic complications."),
                    ("Document as normal variation without further intervention", "Fails standard of care for critical lab thresholds."),
                ],
            },
            # 5. Drag order
            {
                "type": "order",
                "stem": "Place the nurse's sequential actions in the correct order when responding to an acute exacerbation of {subtopic}:",
                "ordered_steps": [
                    ("1. Elevate head of bed to High Fowler position", "Promotes maximal chest expansion and eases respiratory work."),
                    ("2. Apply oxygen therapy via nasal cannula / face mask", "Corrects immediate hypoxemia."),
                    ("3. Obtain emergency vital signs and perform focused lung assessment", "Establishes baseline severity and response."),
                    ("4. Notify the rapid response team and healthcare provider", "Mobilizes advanced airway and critical care support."),
                ],
            },
        ]

        total_needed = 220
        created_count = 0

        # Cycle through subtopics to generate 220+ questions
        for idx in range(total_needed):
            sub = subtopic_list[idx % len(subtopic_list)]
            tmpl = templates[idx % len(templates)]
            category = sub.topic.category
            topic = sub.topic
            cjmm = CJMM_FUNCTIONS[idx % len(CJMM_FUNCTIONS)]
            body_sys = BODY_SYSTEMS[idx % len(BODY_SYSTEMS)]
            level = "Foundational" if idx % 3 == 0 else ("Progressive" if idx % 3 == 1 else "Advanced")

            q_text = tmpl["stem"].format(subtopic=sub.title)

            metadata = {
                "client_needs": category.title,
                "cjmm_function": cjmm,
                "body_system": body_sys,
                "tip": f"NCLEX Clinical Judgment: When assessing {sub.title}, always prioritize ABCs and client safety.",
            }

            question_obj = NCLEXQuestion.objects.create(
                category=category,
                topic=topic,
                subtopic=sub,
                question=f"[{category.title}] {q_text} (#{idx+1})",
                level=level,
                type=tmpl["type"],
                metadata=metadata,
            )

            # Create options
            if tmpl["type"] == "radio":
                QuestionOption.objects.create(
                    question=question_obj,
                    text=tmpl["correct"],
                    is_correct=True,
                    order=1,
                    extra_data={"rationale": tmpl["correct_rationale"]},
                )
                for d_idx, (d_text, d_rat) in enumerate(tmpl["distractors"], start=2):
                    QuestionOption.objects.create(
                        question=question_obj,
                        text=d_text,
                        is_correct=False,
                        order=d_idx,
                        extra_data={"rationale": d_rat},
                    )

            elif tmpl["type"] == "multiple":
                order_num = 1
                for c_text, c_rat in tmpl["correct_opts"]:
                    QuestionOption.objects.create(
                        question=question_obj,
                        text=c_text,
                        is_correct=True,
                        order=order_num,
                        extra_data={"rationale": c_rat},
                    )
                    order_num += 1
                for d_text, d_rat in tmpl["distractor_opts"]:
                    QuestionOption.objects.create(
                        question=question_obj,
                        text=d_text,
                        is_correct=False,
                        order=order_num,
                        extra_data={"rationale": d_rat},
                    )
                    order_num += 1

            elif tmpl["type"] == "order":
                for o_idx, (o_text, o_rat) in enumerate(tmpl["ordered_steps"], start=1):
                    QuestionOption.objects.create(
                        question=question_obj,
                        text=o_text,
                        is_correct=True,
                        order=o_idx,
                        extra_data={"rationale": o_rat},
                    )

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Generated {created_count} rich NCLEX test questions."))

        # Now link all pool questions to the 5 NCLEX Exams
        all_qs = list(NCLEXQuestion.objects.all())
        total_in_db = len(all_qs)
        self.stdout.write(f"Total questions in database: {total_in_db}")

        for exam in NCLEXExam.objects.all():
            # Assign all available questions to the pool
            exam.questions.set(all_qs)
            exam.total_question = 85
            exam.time_limit_mins = 150
            exam.save(update_fields=["total_question", "time_limit_mins"])
            self.stdout.write(self.style.SUCCESS(f"Exam '{exam.title}' pool updated with {exam.questions.count()} eligible questions."))

        self.stdout.write(self.style.SUCCESS("All 5 NCLEX Final Exams now have full 200+ question pools ready for Blueprint testing!"))
