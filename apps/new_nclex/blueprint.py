import random
from collections import defaultdict
from .models import NCLEXQuestion


# Default NCLEX-RN Blueprint Target Distribution (for 85 total questions)
DEFAULT_BLUEPRINT = {
    "Management of Care": 17,
    "Safety and Infection Control": 10,
    "Health Promotion and Maintenance": 7,
    "Psychosocial Integrity": 7,
    "Basic Care and Comfort": 7,
    "Pharmacological and Parenteral Therapies": 13,
    "Reduction of Risk Potential": 10,
    "Physiological Adaptation": 14,
}


def generate_exam_questions(exam, target_count=85):
    """
    Selects a balanced set of questions (default 85) from the exam's question pool
    using the blueprint specification while keeping unfolding case studies grouped.
    Returns a deterministic list of question IDs for the attempt.
    """
    pool_qs = list(exam.questions.select_related("category", "topic", "subtopic").all())
    if not pool_qs:
        return []

    total_in_pool = len(pool_qs)
    # If pool is smaller than or equal to target, return all pool questions randomized
    if total_in_pool <= target_count:
        random.shuffle(pool_qs)
        return [q.id for q in pool_qs]

    # Separate standalone questions and case studies
    case_studies = defaultdict(list)
    standalone_questions = []

    for q in pool_qs:
        case_id = q.metadata.get("case_study_id") if isinstance(q.metadata, dict) else None
        if case_id:
            case_studies[case_id].append(q)
        else:
            standalone_questions.append(q)

    # Sort questions within each case study by sequence/order
    for case_id in case_studies:
        case_studies[case_id].sort(
            key=lambda item: (
                item.metadata.get("case_study_order", 0) if isinstance(item.metadata, dict) else 0,
                item.id,
            )
        )

    selected_questions = []
    selected_ids = set()

    # Step 1: Include up to 2-3 unfolding case studies if available (e.g. 1-2 cases = 6-12 questions)
    available_case_ids = list(case_studies.keys())
    random.shuffle(available_case_ids)

    for case_id in available_case_ids:
        case_items = case_studies[case_id]
        if len(selected_questions) + len(case_items) <= target_count:
            selected_questions.extend(case_items)
            for item in case_items:
                selected_ids.add(item.id)

    # Step 2: Bucket remaining standalone questions by Client Needs category
    category_buckets = defaultdict(list)
    for q in standalone_questions:
        if q.id not in selected_ids:
            cat_name = (
                q.metadata.get("client_needs")
                if isinstance(q.metadata, dict) and q.metadata.get("client_needs")
                else (q.category.title if q.category else "Unassigned")
            )
            category_buckets[cat_name].append(q)

    # Shuffle within each bucket for randomization
    for cat_name in category_buckets:
        random.shuffle(category_buckets[cat_name])

    blueprint = exam.blueprint or DEFAULT_BLUEPRINT
    needed_count = target_count - len(selected_questions)

    # Sample according to blueprint targets
    for cat_name, target in blueprint.items():
        if needed_count <= 0:
            break
        available_in_bucket = category_buckets.get(cat_name, [])
        to_take = min(target, len(available_in_bucket), needed_count)
        for i in range(to_take):
            q = available_in_bucket.pop()
            selected_questions.append(q)
            selected_ids.add(q.id)
            needed_count -= 1

    # Step 3: If still under target_count, backfill from any remaining questions in pool
    if needed_count > 0:
        remaining_pool = [q for q in pool_qs if q.id not in selected_ids]
        random.shuffle(remaining_pool)
        for q in remaining_pool[:needed_count]:
            selected_questions.append(q)
            selected_ids.add(q.id)

    # Preserve case study blocks while allowing standalone item shuffling
    # Build blocks where case studies remain intact
    blocks = []
    current_case_id = None
    current_block = []

    for q in selected_questions:
        case_id = q.metadata.get("case_study_id") if isinstance(q.metadata, dict) else None
        if case_id:
            if current_case_id == case_id:
                current_block.append(q.id)
            else:
                if current_block:
                    blocks.append(current_block)
                current_case_id = case_id
                current_block = [q.id]
        else:
            if current_block:
                blocks.append(current_block)
                current_block = []
                current_case_id = None
            blocks.append([q.id])

    if current_block:
        blocks.append(current_block)

    # Shuffle the blocks
    random.shuffle(blocks)

    # Flatten final question IDs
    final_ids = [qid for block in blocks for qid in block]
    return final_ids[:target_count]
