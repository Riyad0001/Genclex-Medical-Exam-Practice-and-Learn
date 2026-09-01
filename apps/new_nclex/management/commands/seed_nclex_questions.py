"""Seed a starter NCLEX question bank.

Each topic deliberately contains ten questions and every supported question
format, allowing it to be used on its own in a short practice session. The
command is safe to run more than once.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.new_nclex.models import (
    NCLEXCategory,
    NCLEXQuestion,
    NCLEXSubtopic,
    NCLEXTopic,
    QuestionOption,
)


# category, topic, subtopic, subtopic description, questions
# Every question is (stem, choices, zero-based correct choice, level, rationale).
QUESTION_BANK = [
    (
        "Fundamentals of Nursing",
        "Client Safety",
        "Fall Prevention",
        "Measures that reduce a hospitalized client's risk of falling.",
        [
            ("Which intervention is the priority for a client at high risk for falls?", ["Keep the bed in the lowest position with the call light within reach.", "Apply four side rails at all times.", "Encourage the client to walk without assistance.", "Place frequently used items on the top shelf."], 0, "Beginner", "A low bed and accessible call light reduce injury risk while preserving the client's ability to request help."),
            ("A client begins to fall while walking with the nurse. What should the nurse do first?", ["Widen stance and guide the client safely to the floor.", "Try to hold the client upright.", "Leave to obtain a wheelchair.", "Pull the client back toward the bed."], 0, "Intermediate", "Guiding the client to the floor protects both the client and nurse; attempting to stop the fall can cause injury."),
            ("Which finding requires the nurse to implement fall precautions immediately?", ["The client received an opioid analgesic 30 minutes ago.", "The client requests water with meals.", "The client wears reading glasses.", "The client has a visitor at the bedside."], 0, "Beginner", "Opioids can cause sedation and orthostatic hypotension, increasing the immediate fall risk."),
            ("Which statement by an unlicensed assistive personnel (UAP) indicates correct understanding of fall prevention?", ["I will make sure the client's nonskid footwear is on before ambulation.", "I will raise all four side rails before leaving the room.", "I will silence the bed alarm if it sounds repeatedly.", "I will encourage the client to get up quickly after lying down."], 0, "Beginner", "Nonskid footwear is an appropriate UAP intervention; four side rails can be considered a restraint."),
            ("A confused client repeatedly attempts to get out of bed. Which intervention should the nurse try first?", ["Use a bed-exit alarm and frequent rounding.", "Apply wrist restraints.", "Request a sedative prescription.", "Move the client to a private room."], 0, "Intermediate", "Least restrictive measures, such as alarms and observation, are used before restraints or sedatives."),
            ("Which client should the nurse assess first for fall risk?", ["An older adult who reports dizziness when standing.", "An adult with a healed forearm fracture.", "A young adult awaiting discharge instructions.", "An adult receiving a high-fiber diet."], 0, "Advanced", "Postural dizziness may indicate orthostatic hypotension and creates an immediate risk of falling."),
        ],
    ),
    (
        "Fundamentals of Nursing",
        "Infection Prevention",
        "Standard and Transmission-Based Precautions",
        "Actions that prevent healthcare-associated infections and transmission.",
        [
            ("What is the most effective action for preventing the spread of infection between clients?", ["Perform hand hygiene before and after client contact.", "Wear a surgical mask for every interaction.", "Change gloves once per shift.", "Give antibiotics before obtaining cultures."], 0, "Beginner", "Hand hygiene is the single most effective way to reduce transmission of microorganisms."),
            ("Which personal protective equipment should the nurse don first when entering a room requiring contact precautions?", ["Gown", "Gloves", "Mask", "Face shield"], 0, "Intermediate", "For contact precautions, don the gown first, followed by gloves over the gown cuffs."),
            ("A client has suspected pulmonary tuberculosis. Which precaution is required?", ["Airborne precautions in a negative-pressure room.", "Droplet precautions in a semi-private room.", "Contact precautions with a surgical mask.", "Protective isolation with positive pressure."], 0, "Beginner", "Tuberculosis is transmitted by airborne particles and requires a negative-pressure room and respirator."),
            ("When should the nurse use soap and water instead of alcohol-based hand rub?", ["When hands are visibly soiled.", "Before taking a blood pressure.", "After touching intact skin.", "When entering any client room."], 0, "Beginner", "Soap and water physically removes visible soil and is required for certain organisms such as C. difficile."),
            ("Which action breaks sterile technique?", ["Holding a sterile object below waist level.", "Keeping the sterile field in view.", "Adding sterile supplies from a short distance above the field.", "Considering the outer one-inch border contaminated."], 0, "Intermediate", "Anything below the waist is out of view and considered contaminated."),
            ("A client with C. difficile diarrhea requires which additional intervention?", ["Wash hands with soap and water after removing gloves.", "Use only a standard surgical mask.", "Place the client in a negative-pressure room.", "Discard all linen in a red biohazard bag."], 0, "Advanced", "C. difficile spores are not reliably removed by alcohol hand rub; soap and water is required."),
        ],
    ),
    (
        "Fundamentals of Nursing",
        "Assessment and Vital Signs",
        "Clinical Assessment",
        "Foundational nursing assessment and interpretation of vital signs.",
        [
            ("Which assessment finding should the nurse report immediately?", ["Oxygen saturation of 86% on room air.", "Oral temperature of 37.2 C (99 F).", "Heart rate of 82/min after resting.", "Blood pressure of 128/76 mm Hg."], 0, "Beginner", "An oxygen saturation of 86% indicates significant hypoxemia and needs prompt assessment and intervention."),
            ("The nurse obtains a blood pressure of 88/54 mm Hg for a client who is pale and dizzy. What is the priority action?", ["Assess the client and recheck the blood pressure.", "Document the reading as expected.", "Offer a caffeinated beverage.", "Wait until the next scheduled vital signs."], 0, "Intermediate", "Hypotension with symptoms can signal poor perfusion; assess and validate the finding promptly."),
            ("Where should the nurse place the stethoscope to auscultate the apical pulse?", ["Fifth intercostal space at the left midclavicular line.", "Second intercostal space at the right sternal border.", "Fourth intercostal space at the right midclavicular line.", "Sixth intercostal space at the left sternal border."], 0, "Beginner", "The adult apical pulse is auscultated at the fifth left intercostal space along the midclavicular line."),
            ("Which finding is expected when assessing an adult client's pupils?", ["Equal pupils that constrict briskly to light.", "Fixed pupils of unequal size after a dark room adjustment.", "Pupils that dilate in response to light.", "Absent accommodation when focusing on a near object."], 0, "Beginner", "Normal pupils are equal, round, and reactive to light and accommodation."),
            ("Before obtaining an orthostatic blood pressure, which instruction is appropriate?", ["Assist the client to change positions slowly.", "Ask the client to drink 500 mL of water.", "Have the client walk for five minutes.", "Measure only while the client is standing."], 0, "Intermediate", "Measurements are compared across positions, and slow position changes help prevent injury from dizziness."),
            ("Which assessment technique is appropriate for an abdomen?", ["Auscultate before palpating.", "Palpate deeply before inspection.", "Percuss before inspection.", "Perform rebound tenderness first."], 0, "Advanced", "Auscultation is done before palpation or percussion because manipulation can alter bowel sounds."),
        ],
    ),
    (
        "Adult Health Nursing",
        "Cardiovascular Care",
        "Acute Coronary Syndrome",
        "Recognition and early nursing care of acute cardiac conditions.",
        [
            ("A client reports crushing chest pain and diaphoresis. Which action is the priority?", ["Obtain a 12-lead ECG and assess vital signs.", "Offer the client a meal.", "Encourage deep breathing for 30 minutes.", "Place the client flat in bed."], 0, "Advanced", "Possible acute coronary syndrome requires rapid assessment, including an ECG and vital signs."),
            ("Which finding is most consistent with left-sided heart failure?", ["Crackles in the lungs.", "Jugular vein distention only.", "Dependent ankle edema only.", "Enlarged liver."], 0, "Intermediate", "Left-sided failure causes pulmonary congestion, commonly producing crackles and dyspnea."),
            ("Before administering nitroglycerin for chest pain, which finding should cause the nurse to hold the medication?", ["Blood pressure of 86/54 mm Hg.", "Heart rate of 88/min.", "Respiratory rate of 18/min.", "Temperature of 37 C (98.6 F)."], 0, "Intermediate", "Nitroglycerin lowers blood pressure and should be withheld for significant hypotension."),
            ("Which statement by a client taking warfarin indicates understanding of teaching?", ["I will report black, tarry stools.", "I will take aspirin for a headache without asking.", "I will double the next dose if I miss one.", "I will stop the medication when bruising improves."], 0, "Beginner", "Black, tarry stools can indicate gastrointestinal bleeding and must be reported promptly."),
            ("A client with heart failure gains 1.4 kg (3 lb) in two days. What should the nurse do?", ["Notify the provider of possible fluid retention.", "Reassure the client that this is expected.", "Encourage additional oral fluids.", "Hold the prescribed diuretic."], 0, "Intermediate", "Rapid weight gain is a sensitive sign of fluid retention and worsening heart failure."),
            ("Which assessment is the best indicator of fluid status in a client with heart failure?", ["Daily weight at the same time on the same scale.", "Skin turgor once per shift.", "Capillary refill every four hours.", "Pupil size before meals."], 0, "Beginner", "Consistent daily weights provide the most reliable measure of fluid gain or loss."),
        ],
    ),
    (
        "Adult Health Nursing",
        "Respiratory Care",
        "Oxygenation and Ventilation",
        "Assessment and management of impaired gas exchange and ventilation.",
        [
            ("A client with COPD is short of breath. Which position best promotes ventilation?", ["High-Fowler's position.", "Trendelenburg position.", "Supine with legs elevated.", "Prone with the head flat."], 0, "Beginner", "High-Fowler's position promotes chest expansion and makes breathing easier."),
            ("Which finding indicates that oxygen therapy is effective?", ["Oxygen saturation increases from 86% to 94%.", "Respiratory rate increases from 18 to 34/min.", "The client becomes increasingly restless.", "The client develops cyanosis around the lips."], 0, "Beginner", "An increased oxygen saturation indicates improved oxygenation."),
            ("A client suddenly develops dyspnea after central-line insertion. Which finding is most concerning?", ["Absent breath sounds on one side.", "Mild thirst.", "Bowel sounds in all quadrants.", "Warm, dry skin."], 0, "Advanced", "Sudden unilateral absent breath sounds may indicate a pneumothorax, a complication requiring immediate action."),
            ("Which instruction should the nurse give a client using an incentive spirometer?", ["Inhale slowly and deeply, then hold the breath briefly.", "Blow out forcefully into the mouthpiece.", "Use the device once each day.", "Lie flat while using the device."], 0, "Beginner", "Slow deep inhalation and a short breath hold expand alveoli and help prevent atelectasis."),
            ("Which finding in a client with asthma requires immediate intervention?", ["A silent chest with severe respiratory distress.", "Expiratory wheezes that improve after inhaler use.", "A respiratory rate of 20/min.", "A productive cough with clear mucus."], 0, "Advanced", "A silent chest can indicate minimal air movement and impending respiratory failure."),
            ("A client receiving oxygen by nasal cannula reports dry nasal passages. What should the nurse do?", ["Use a humidification device as prescribed.", "Increase the flow rate without an order.", "Discontinue oxygen therapy.", "Apply petroleum jelly inside the nares."], 0, "Intermediate", "Humidification can reduce dryness; petroleum products are avoided because of fire risk with oxygen."),
        ],
    ),
    (
        "Adult Health Nursing",
        "Endocrine Care",
        "Diabetes Management",
        "Nursing care, monitoring, and teaching for diabetes mellitus.",
        [
            ("A conscious client has a blood glucose of 58 mg/dL. What should the nurse give first?", ["15 g of rapid-acting carbohydrate.", "A dose of long-acting insulin.", "A high-protein meal only.", "Nothing by mouth for one hour."], 0, "Beginner", "A conscious client with hypoglycemia needs rapid-acting carbohydrate followed by reassessment in about 15 minutes."),
            ("Which finding is most characteristic of diabetic ketoacidosis?", ["Deep, rapid respirations.", "Bradycardia with hypertension.", "Cold, dry skin with pinpoint pupils.", "Weight gain and edema."], 0, "Intermediate", "Kussmaul respirations are a compensatory response to metabolic acidosis in diabetic ketoacidosis."),
            ("Which insulin can be administered intravenously in an emergency?", ["Regular insulin.", "Insulin glargine.", "Insulin detemir.", "NPH insulin."], 0, "Intermediate", "Regular insulin is the standard insulin used intravenously for urgent glycemic management."),
            ("Which statement shows correct foot-care teaching for a client with diabetes?", ["I will inspect my feet every day.", "I will walk barefoot indoors to strengthen my feet.", "I will use a heating pad for cold feet.", "I will trim corns with a blade."], 0, "Beginner", "Daily inspection helps identify injuries early; clients should avoid burns, trauma, and self-treatment of corns."),
            ("A client who is NPO for surgery has a blood glucose of 320 mg/dL. What is the priority nursing action?", ["Notify the provider and follow the prescribed insulin protocol.", "Give the client orange juice.", "Hold all glucose monitoring.", "Administer the usual meal-time insulin without checking."], 0, "Advanced", "Marked hyperglycemia in an NPO client requires provider-directed treatment and close monitoring."),
            ("Which symptom should a client identify as possible hypoglycemia?", ["Shakiness and sweating.", "Increased thirst and frequent urination.", "Slow wound healing.", "Fruity breath odor."], 0, "Beginner", "Adrenergic symptoms such as tremors and diaphoresis commonly occur with hypoglycemia."),
        ],
    ),
    (
        "Maternal-Child Nursing",
        "Antepartum Care",
        "Prenatal Assessment",
        "Assessment, education, and warning signs during pregnancy.",
        [
            ("Which symptom during pregnancy should the client report immediately?", ["Vaginal bleeding.", "Mild nausea in the morning.", "Increased appetite in the second trimester.", "Darkening of the areolae."], 0, "Beginner", "Vaginal bleeding may indicate a serious complication and requires immediate evaluation."),
            ("A pregnant client is Rh-negative. Which medication may be prescribed to prevent sensitization?", ["Rho(D) immune globulin.", "Oxytocin.", "Magnesium sulfate.", "Terbutaline."], 0, "Intermediate", "Rho(D) immune globulin helps prevent maternal antibody formation against Rh-positive blood."),
            ("Which finding is most concerning in a client at 34 weeks of gestation?", ["Severe headache and blurred vision.", "Mild ankle edema at the end of the day.", "Urinary frequency.", "Occasional heartburn after meals."], 0, "Advanced", "Headache and visual changes can signal severe preeclampsia and require prompt assessment."),
            ("Which instruction promotes fetal well-being in a client who is 28 weeks pregnant?", ["Report a noticeable decrease in fetal movement.", "Avoid all exercise for the remainder of pregnancy.", "Sleep only flat on the back.", "Restrict fluid intake after noon."], 0, "Beginner", "A reduction in fetal movement can indicate compromised fetal status and should be reported."),
            ("A client asks why folic acid is recommended before and during early pregnancy. What is the best response?", ["It helps reduce the risk of neural tube defects.", "It prevents gestational diabetes.", "It guarantees a full-term birth.", "It eliminates morning sickness."], 0, "Beginner", "Adequate folic acid before conception and early in pregnancy lowers neural tube defect risk."),
            ("Which food should the nurse advise a pregnant client to avoid?", ["Unpasteurized soft cheese.", "Pasteurized yogurt.", "Fully cooked eggs.", "Washed fresh fruit."], 0, "Intermediate", "Unpasteurized products can carry pathogens such as Listeria that can harm the fetus."),
        ],
    ),
    (
        "Maternal-Child Nursing",
        "Newborn Care",
        "Immediate Newborn Assessment",
        "Essential assessment and safety care during the newborn period.",
        [
            ("Which action is the priority immediately after birth for a vigorous newborn?", ["Dry and warm the newborn.", "Give the first bath.", "Measure head circumference.", "Obtain footprints before assessment."], 0, "Beginner", "Drying and warming reduce heat loss and support the newborn's transition to extrauterine life."),
            ("Which finding in a newborn should the nurse report promptly?", ["Central cyanosis.", "Acrocyanosis of hands and feet shortly after birth.", "Milia on the nose.", "A temporary swollen scalp after vaginal birth."], 0, "Intermediate", "Central cyanosis may signal inadequate oxygenation, unlike common transient acrocyanosis."),
            ("Which statement by a parent shows correct understanding of safe sleep?", ["I will place my baby on the back to sleep in an empty crib.", "I will place pillows around my baby for support.", "I will let my baby sleep in my bed after feeding.", "I will place my baby on the stomach after midnight."], 0, "Beginner", "Back sleeping on a firm, empty sleep surface reduces the risk of sleep-related infant death."),
            ("A newborn has a temperature of 36.1 C (97 F). What is the nurse's first action?", ["Place the newborn skin-to-skin with a warm blanket.", "Give a cold sponge bath.", "Offer sterile water.", "Move the newborn away from the parent."], 0, "Intermediate", "Skin-to-skin contact and warming measures treat mild cold stress and reduce further heat loss."),
            ("Which sign suggests dehydration in a newborn?", ["Fewer wet diapers than expected.", "A brief episode of hiccups.", "Sneezing after feeding.", "A small amount of breast swelling."], 0, "Beginner", "Inadequate urine output is an important indicator of possible dehydration or insufficient intake."),
            ("Which action verifies newborn identity before a procedure?", ["Compare the newborn's identification band with the parent's band.", "Ask the parent to state the newborn's room number.", "Use the newborn's bassinet color.", "Verify only the newborn's last name."], 0, "Beginner", "Matching identification bands is the standard safety check before care or procedures."),
        ],
    ),
    (
        "Maternal-Child Nursing",
        "Pediatric Care",
        "Medication and Hydration Safety",
        "Safe assessment and care priorities for infants and children.",
        [
            ("Which finding is an early sign of dehydration in a child with diarrhea?", ["Decreased urine output.", "Bradycardia.", "Generalized edema.", "Increased tears when crying."], 0, "Intermediate", "Reduced urine output is an early and useful indicator of dehydration in children."),
            ("Which action is most important before giving an oral medication to a child?", ["Verify the dose using the child's current weight.", "Ask the parent to estimate the dose.", "Mix the medication into a full bottle of formula.", "Tell the child it is candy."], 0, "Beginner", "Many pediatric doses are weight based; current weight must be used to verify a safe dose."),
            ("A child with suspected epiglottitis is drooling and sitting forward. Which action should the nurse avoid?", ["Using a tongue depressor to inspect the throat.", "Keeping the child calm with a parent present.", "Preparing emergency airway equipment.", "Notifying the provider immediately."], 0, "Advanced", "Throat examination can trigger complete airway obstruction in a child with suspected epiglottitis."),
            ("Which intervention best reduces pain from an intramuscular injection in a toddler?", ["Have the parent comfort and hold the child securely.", "Tell the child not to cry.", "Delay the injection until the child sleeps.", "Use the smallest possible volume regardless of prescription."], 0, "Beginner", "Parental presence, secure positioning, and age-appropriate comfort measures reduce distress and promote safety."),
            ("Which symptom in an infant with vomiting requires immediate evaluation?", ["A sunken fontanelle and lethargy.", "One small spit-up after feeding.", "Hiccups after burping.", "Sleeping after a usual feeding."], 0, "Advanced", "Lethargy and a sunken fontanelle suggest significant dehydration and possible circulatory compromise."),
            ("Which instruction should the nurse give a parent about acetaminophen?", ["Use the dosing device that comes with the medication.", "Give aspirin if the fever continues.", "Measure doses with a household spoon.", "Double the dose for a high fever."], 0, "Beginner", "The supplied dosing device helps prevent dosing errors; aspirin is avoided in children because of Reye syndrome risk."),
        ],
    ),
]

# One configuration for each topic.  These create the non-radio question
# formats while the main bank above provides the topic-specific radio items.
TOPIC_TYPE_DETAILS = {
    "Client Safety": {
        "actions": ["Keep the bed low and the call light within reach.", "Use nonskid footwear before ambulation.", "Raise all four side rails.", "Encourage an unassisted dizzy client to walk."],
        "steps": ["Assess the client for injury.", "Call for assistance if needed.", "Guide the client safely to the floor.", "Document and report the event."],
        "term": "safety",
        "priority": "keep the bed low and the call light within reach",
    },
    "Infection Prevention": {
        "actions": ["Perform hand hygiene before client contact.", "Remove PPE before leaving the room.", "Reuse gloves between clients.", "Place used needles in regular trash."],
        "steps": ["Perform hand hygiene.", "Don the gown.", "Don gloves over the gown cuffs.", "Enter the room."],
        "term": "hand hygiene",
        "priority": "perform hand hygiene before and after client contact",
    },
    "Assessment and Vital Signs": {
        "actions": ["Compare findings with the client's baseline.", "Reassess an unexpected vital sign.", "Ignore a symptomatic low blood pressure.", "Document a value before measuring it."],
        "steps": ["Inspect the abdomen.", "Auscultate bowel sounds.", "Percuss the abdomen.", "Palpate the abdomen."],
        "term": "assessment",
        "priority": "assess oxygenation when the oxygen saturation is low",
    },
    "Cardiovascular Care": {
        "actions": ["Obtain daily weights for heart failure.", "Report black, tarry stools with warfarin use.", "Give nitroglycerin to a hypotensive client.", "Double a missed warfarin dose."],
        "steps": ["Assess chest pain and vital signs.", "Obtain a 12-lead ECG.", "Notify the provider or rapid-response team.", "Administer prescribed treatment."],
        "term": "perfusion",
        "priority": "obtain an ECG for new crushing chest pain",
    },
    "Respiratory Care": {
        "actions": ["Place a dyspneic client in High-Fowler's position.", "Encourage prescribed incentive-spirometer use.", "Apply petroleum jelly inside the nares with oxygen.", "Ignore a silent chest in severe asthma."],
        "steps": ["Assess airway and breathing.", "Position the client upright.", "Apply prescribed oxygen.", "Reassess oxygen saturation and work of breathing."],
        "term": "oxygenation",
        "priority": "assess airway and breathing first",
    },
    "Endocrine Care": {
        "actions": ["Inspect feet every day.", "Carry a source of rapid-acting carbohydrate.", "Walk barefoot to strengthen the feet.", "Use a heating pad on numb feet."],
        "steps": ["Check the blood glucose.", "Give 15 g of rapid-acting carbohydrate.", "Recheck blood glucose in 15 minutes.", "Provide a snack if the next meal is delayed."],
        "term": "hypoglycemia",
        "priority": "give rapid-acting carbohydrate to a conscious client with low blood glucose",
    },
    "Antepartum Care": {
        "actions": ["Report vaginal bleeding promptly.", "Report decreased fetal movement.", "Consume unpasteurized soft cheese.", "Lie flat on the back for long periods."],
        "steps": ["Assess the client reporting severe headache.", "Check blood pressure and other vital signs.", "Notify the provider of concerning findings.", "Prepare for prescribed treatment and monitoring."],
        "term": "preeclampsia",
        "priority": "report vaginal bleeding immediately",
    },
    "Newborn Care": {
        "actions": ["Place the newborn on the back in an empty crib.", "Compare newborn and parent identification bands.", "Use pillows in the crib for positioning.", "Place the newborn prone for sleep."],
        "steps": ["Dry the newborn thoroughly.", "Place the newborn skin-to-skin with the parent.", "Cover with a warm blanket.", "Reassess temperature."],
        "term": "thermoregulation",
        "priority": "place the newborn on the back to sleep in an empty crib",
    },
    "Pediatric Care": {
        "actions": ["Verify medication doses using current weight.", "Use the supplied medication dosing device.", "Measure medicine with a household spoon.", "Give aspirin for a child's fever."],
        "steps": ["Assess the child's airway and breathing.", "Keep the child calm with a parent present.", "Prepare emergency equipment if indicated.", "Notify the provider of urgent findings."],
        "term": "dehydration",
        "priority": "verify a medication dose using the child's current weight",
    },
}


class Command(BaseCommand):
    help = "Seed 90 NCLEX questions across 3 categories and 9 topics."

    @transaction.atomic
    def handle(self, *args, **options):
        created_questions = 0
        updated_questions = 0

        for category_title, topic_title, subtopic_title, description, questions in QUESTION_BANK:
            category, _ = NCLEXCategory.objects.get_or_create(title=category_title)
            topic, _ = NCLEXTopic.objects.get_or_create(
                category=category,
                title=topic_title,
            )
            subtopic, _ = NCLEXSubtopic.objects.get_or_create(
                topic=topic,
                title=subtopic_title,
                defaults={"description": description},
            )

            # Keep the description useful if the command is rerun after a change.
            if subtopic.description != description:
                subtopic.description = description
                subtopic.save(update_fields=["description"])

            for stem, choices, correct_index, level, rationale in questions:
                question, created = NCLEXQuestion.objects.get_or_create(
                    category=category,
                    topic=topic,
                    subtopic=subtopic,
                    question=stem,
                    defaults={
                        "level": level,
                        "type": "radio",
                        "note": rationale,
                        "metadata": {"seed": "nclex_starter_bank"},
                    },
                )
                if created:
                    created_questions += 1
                else:
                    updated_questions += 1

                for order, choice in enumerate(choices, start=1):
                    QuestionOption.objects.update_or_create(
                        question=question,
                        order=order,
                        defaults={
                            "text": choice,
                            "is_correct": order - 1 == correct_index,
                        },
                    )

            details = TOPIC_TYPE_DETAILS[topic_title]
            type_questions = [
                (
                    "multiple",
                    f"For {topic_title}, which actions are appropriate? Select all that apply.",
                    details["actions"],
                    {0, 1},
                    "Intermediate",
                    "The first two actions support safe, evidence-based nursing care; the remaining actions are unsafe.",
                    {},
                    None,
                ),
                (
                    "order",
                    f"Place these {topic_title.lower()} nursing actions in the correct order.",
                    details["steps"],
                    {0, 1, 2, 3},
                    "Advanced",
                    "Start with assessment, then implement immediate safety measures, communicate urgent findings, and continue monitoring.",
                    {},
                    None,
                ),
                (
                    "input",
                    f"Enter the key clinical term most closely associated with this {topic_title.lower()} review.",
                    [details["term"]],
                    {0},
                    "Beginner",
                    f"The expected answer is '{details['term']}'.",
                    {"unit": ""},
                    None,
                ),
                (
                    "highlight",
                    f"Highlight the priority action for {topic_title.lower()}.",
                    [details["priority"], "delay the assessment until the next routine round", "ask the client to manage the concern independently", "document the concern without taking action"],
                    {0},
                    "Intermediate",
                    "The highlighted priority action addresses the most urgent client need.",
                    {},
                    f"During clinical care, the nurse should {details['priority']}. The nurse should not delay assessment, leave the client to manage an urgent concern, or only document without acting.",
                ),
            ]

            for question_type, stem, choices, correct_indexes, level, rationale, metadata, passage in type_questions:
                question, created = NCLEXQuestion.objects.update_or_create(
                    category=category,
                    topic=topic,
                    subtopic=subtopic,
                    question=stem,
                    defaults={
                        "level": level,
                        "type": question_type,
                        "note": rationale,
                        "metadata": {"seed": "nclex_starter_bank", **metadata},
                        "passage": passage,
                    },
                )
                if created:
                    created_questions += 1
                else:
                    updated_questions += 1

                for order, choice in enumerate(choices, start=1):
                    QuestionOption.objects.update_or_create(
                        question=question,
                        order=order,
                        defaults={
                            "text": choice,
                            "is_correct": order - 1 in correct_indexes,
                        },
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "NCLEX question bank seeded: "
                f"{created_questions} created, {updated_questions} already present. "
                "Each of 9 topics contains 10 questions and all five question types "
                "(90 total)."
            )
        )
