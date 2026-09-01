from collections import defaultdict


def calculate_readiness_level(score_percentage):
    """Determine NCLEX readiness tier and description based on score percentage."""
    if score_percentage >= 78.0:
        return {
            "level": "Strong Readiness",
            "tier": "high",
            "description": "High probability of passing the NCLEX on the first attempt under current performance standards.",
        }
    elif score_percentage >= 65.0:
        return {
            "level": "Approaching Readiness",
            "tier": "moderate",
            "description": "Moderate readiness. Targeted review in weak client need categories is recommended before the final exam.",
        }
    else:
        return {
            "level": "Developing",
            "tier": "low",
            "description": "Foundational review required across clinical concepts, pharmacology, and prioritization frameworks.",
        }


def compute_category_breakdown(items_by_key):
    """
    Given a dict of key -> list of boolean is_correct values,
    returns a sorted list of performance statistics.
    """
    results = []
    for key, correct_list in items_by_key.items():
        if not key or key == "Unassigned":
            continue
        total = len(correct_list)
        correct = sum(correct_list)
        pct = round((correct / total) * 100, 1) if total > 0 else 0.0
        results.append({
            "name": key,
            "total_questions": total,
            "correct_answers": correct,
            "score_percentage": pct,
        })
    results.sort(key=lambda x: x["score_percentage"], reverse=True)
    return results


def build_detailed_analytics(questions, results_by_question_id):
    """
    Builds multi-dimensional post-exam performance analysis across:
    - Client Needs Categories
    - Clinical Judgment Functions (CJMM)
    - Body Systems / Specialty areas
    - Strengths and Priority Improvement recommendations
    """
    client_needs_map = defaultdict(list)
    cjmm_map = defaultdict(list)
    body_system_map = defaultdict(list)

    total_correct = 0
    total_incorrect = 0
    total_skipped = 0

    for q in questions:
        res = results_by_question_id.get(q.id)
        is_answered = res is not None and not res.is_skipped
        is_corr = res.is_correct if is_answered else False

        if is_answered:
            if is_corr:
                total_correct += 1
            else:
                total_incorrect += 1
        else:
            total_skipped += 1

        meta = q.metadata if isinstance(q.metadata, dict) else {}

        # 1. Client Needs Category
        client_needs_key = (
            meta.get("client_needs")
            or (q.category.title if q.category else "Unassigned")
        )
        client_needs_map[client_needs_key].append(is_corr)

        # 2. Clinical Judgment Function (CJMM)
        cjmm_key = meta.get("cjmm_function")
        if not cjmm_key:
            # Fallback estimation based on level/type if not tagged
            cjmm_key = "Analyze Cues" if q.type == "multiple" else "Recognize Cues"
        cjmm_map[cjmm_key].append(is_corr)

        # 3. Body System / Specialty
        body_system_key = (
            meta.get("body_system")
            or (q.subtopic.title if q.subtopic else (q.topic.title if q.topic else "General Nursing"))
        )
        body_system_map[body_system_key].append(is_corr)

    total_q = len(questions)
    overall_score = round((total_correct / total_q) * 100, 1) if total_q > 0 else 0.0
    readiness = calculate_readiness_level(overall_score)

    client_needs_breakdown = compute_category_breakdown(client_needs_map)
    cjmm_breakdown = compute_category_breakdown(cjmm_map)
    body_system_breakdown = compute_category_breakdown(body_system_map)

    # Calculate Top Strengths (categories >= 75%) & Areas to Improve (< 75%)
    all_scored_categories = []
    for item in client_needs_breakdown + cjmm_breakdown + body_system_breakdown:
        all_scored_categories.append(item)

    # Deduplicate by category name
    seen = set()
    unique_cats = []
    for c in all_scored_categories:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique_cats.append(c)

    unique_cats.sort(key=lambda x: (x["score_percentage"], -x["total_questions"]))

    areas_to_improve = [
        {
            "category": c["name"],
            "score_percentage": c["score_percentage"],
            "total_questions": c["total_questions"],
            "recommendation": f"Practice targeted questions and review study notes for {c['name']}.",
        }
        for c in unique_cats[:3]
    ]

    strengths = [
        {
            "category": c["name"],
            "score_percentage": c["score_percentage"],
            "total_questions": c["total_questions"],
        }
        for c in sorted(unique_cats, key=lambda x: x["score_percentage"], reverse=True)[:3]
    ]

    return {
        "overall_score": overall_score,
        "readiness_level": readiness["level"],
        "readiness_tier": readiness["tier"],
        "readiness_description": readiness["description"],
        "total_questions": total_q,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "total_skipped": total_skipped,
        "passed": overall_score >= 75.0,
        "client_needs_performance": client_needs_breakdown,
        "clinical_judgment_performance": cjmm_breakdown,
        "body_system_performance": body_system_breakdown,
        "strengths": strengths,
        "areas_to_improve": areas_to_improve,
    }
