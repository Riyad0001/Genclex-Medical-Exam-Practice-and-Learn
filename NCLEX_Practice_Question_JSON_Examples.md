# NCLEX Practice Question and Answer JSON Examples

`GET /api/nclex/practice/exam/<session_id>/` returns every question assigned to a practice session. Radio, multiple-select, order, and highlight answers are lists. Input uses a single string. Options are `QuestionOption` records, except that input options are deliberately hidden. The client must never receive `is_correct` before a test is complete.

## Finish a practice session and get results

When the learner presses **Finish Exam**, call:

```
POST /api/nclex/practice/finish/<session_id>/
```

The endpoint is authenticated and only finishes the current user's session. It treats every question without a submitted answer as skipped, saves the summary, and returns a complete review. It is safe to call again to re-open the same results.

```json
{
  "message": "Practice session finished successfully.",
  "session_id": 3,
  "is_finished": true,
  "result": {
    "total_correct_answer": 6,
    "total_incorrect_answer": 2,
    "total_skipped_answer": 2,
    "total_question": 10,
    "total_percentage": 60.0,
    "results": [
      {
        "question_id": 101,
        "title": "Question text",
        "type": "radio",
        "user_answer": {"id": 1001, "text": "Selected answer"},
        "correct_answer": {"id": 1001, "text": "Selected answer"},
        "is_correct": true,
        "is_skipped": false,
        "explanation": "https://api.example.com/media/explanations/101.pdf"
      },
      {
        "question_id": 102,
        "title": "Unanswered question",
        "type": "multiple",
        "user_answer": null,
        "correct_answer": [{"id": 1011, "text": "Correct answer"}],
        "is_correct": false,
        "is_skipped": true,
        "explanation": null
      }
    ]
  }
}
```

## Radio

Question response:

```json
{
  "id": 101,
  "title": "Which intervention reduces fall risk?",
  "type": "radio",
  "level": "Beginner",
  "options": [
    {"id": 1001, "text": "Keep the bed low and call light within reach."},
    {"id": 1002, "text": "Raise all four side rails."}
  ]
}
```

Submit a list containing one option ID:

```json
{"session_id": 3, "question_id": 101, "answer": [1001]}
```

## Multiple Select

Question response contains all options. More than one option can have `is_correct=true` in the database.

```json
{
  "id": 102,
  "type": "multiple",
  "options": [
    {"id": 1011, "text": "Perform hand hygiene."},
    {"id": 1012, "text": "Remove PPE before leaving the room."},
    {"id": 1013, "text": "Reuse gloves between clients."}
  ]
}
```

Submit selected option IDs:

```json
{"session_id": 3, "question_id": 102, "answer": [1011, 1012]}
```

## Order

The response contains options in their stored order. The client may shuffle them visually. Submit every option ID once, in the user-selected order.

```json
{
  "id": 103,
  "type": "order",
  "options": [
    {"id": 1021, "text": "Assess airway and breathing."},
    {"id": 1022, "text": "Position the client upright."},
    {"id": 1023, "text": "Apply prescribed oxygen."}
  ]
}
```

```json
{"session_id": 3, "question_id": 103, "answer": [1021, 1022, 1023]}
```

## Input

Input questions store their correct value as exactly one `QuestionOption` with `is_correct=true`; that option is not included in the GET response. Metadata only stores the fixed unit:

```json
{"unit": "mg"}
```

The response exposes only the unit:

```json
{"id": 104, "type": "input", "unit": "mg", "options": []}
```

Submit one string value:

```json
{"session_id": 3, "question_id": 104, "answer": "10"}
```

## Highlight

Highlight uses the same option model as multiple-select. Each text the user may highlight is a `QuestionOption`; mark the correct text with `is_correct=true`. **No highlight metadata is required.**

```json
{
  "id": 105,
  "type": "highlight",
  "passage": "The nurse should assess airway and breathing first, then position the client upright.",
  "options": [
    {"id": 1031, "text": "assess airway and breathing first"},
    {"id": 1032, "text": "position the client upright"}
  ]
}
```

Submit all highlighted option IDs, just as for multiple-select:

```json
{"session_id": 3, "question_id": 105, "answer": [1031]}
```

The answer is correct only when the submitted option-ID set exactly matches the options marked `is_correct=true`.
