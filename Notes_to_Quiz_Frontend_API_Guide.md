# NCLEX Quiz & Exam System — Frontend API Integration Guide

This document provides the complete API specifications, payload structures, question format rendering rules, live exam answer submissions, score summary overview, and history management endpoints for the NCLEX Quiz system.

---

## 🔐 Base Configuration & Authentication

- **Base URL:** `/api/notes_flashcard/`
- **Authentication:** Bearer Token in Request Header
  ```http
  Authorization: Bearer <your_jwt_access_token>
  ```

---

## 📑 Summary of Endpoints

| Action | HTTP Method | Endpoint Path | Content-Type |
|---|---|---|---|
| **1. Generate NCLEX Quiz** | `POST` | `/api/notes_flashcard/nclex/generate/` | `multipart/form-data` |
| **2. List Quiz History** | `GET` | `/api/notes_flashcard/nclex/` | N/A |
| **3. Get Single Quiz Details** | `GET` | `/api/notes_flashcard/nclex/<id>/` | N/A |
| **4. Submit Question Answer** | `POST` | `/api/notes_flashcard/nclex/<id>/submit/` | `application/json` |
| **5. Get Full Exam Overview / Score** | `GET` | `/api/notes_flashcard/nclex/<id>/score/` | N/A |
| **6. Restart / Retake Exam** | `POST` | `/api/notes_flashcard/nclex/<id>/restart/` | N/A |
| **7. Delete Single Quiz** | `DELETE` | `/api/notes_flashcard/nclex/<id>/delete/` | N/A |
| **8. Delete All Quizzes** | `DELETE` | `/api/notes_flashcard/nclex/clear/` | N/A |

---

## 🚀 1. Generate NCLEX Quiz

Use this endpoint when the user uploads a file or inputs study text to generate a new NCLEX quiz set.

- **URL:** `/api/notes_flashcard/nclex/generate/`
- **Method:** `POST`
- **Headers:** `Content-Type: multipart/form-data`

### Request Parameters (FormData)

| Parameter Name | Data Type | Required | Default | Description / Allowed Values |
|---|---|---|---|---|
| `file` | `File` | Optional* | — | File upload (`.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`) |
| `content_source` | `String` | Optional* | — | Text content pasted by user |
| `program` | `String` | Optional | `"RN"` | Student program: `"LPN"` or `"RN"` |
| `question_format` | `String` | Optional | `"MCQ"` | Question type: `"MCQ"`, `"SATA"`, `"NGN"`, `"FITB"`, `"MIX"` |
| `question_requested` | `Number` | Optional | `10` | Number of questions (Range: `1` to `30`) |

> ⚠️ *Note: At least one of `file` OR `content_source` must be provided.*

### Example Response (201 Created)

```json
{
    "id": 16,
    "program": "RN",
    "question_format": "MCQ",
    "question_requested": 5,
    "total_questions": 5,
    "quiz": [
        {
            "id": 0,
            "question_index": 0,
            "type": "MCQ",
            "question": "Which electrolyte imbalance is most commonly associated with loop diuretic therapy?",
            "options": {
                "A": "Hypernatremia",
                "B": "Hypokalemia",
                "C": "Hypercalcemia",
                "D": "Hypermagnesemia"
            },
            "answer": "B",
            "explanation": "Loop diuretics such as furosemide increase potassium excretion, leading to hypokalemia."
        }
    ],
    "created_at": "2026-08-15T12:00:00.000000Z"
}
```

---

## 🧩 2. Question Formats & Frontend Rendering Guide

Every question inside the `quiz` array contains a `"type"` property. Use this property to render the correct UI component:

### 1. `MCQ` (Standard Multiple Choice)
- **UI Render:** Single choice radio buttons (A, B, C, D).
- **User Answer Format:** `String` (e.g., `"B"`)
- **JSON Structure:**
  ```json
  {
      "type": "MCQ",
      "question": "Which lab value should the nurse check...",
      "options": {
          "A": "Option text 1",
          "B": "Option text 2",
          "C": "Option text 3",
          "D": "Option text 4"
      },
      "answer": "B",
      "explanation": "Explanation text..."
  }
  ```

### 2. `SATA` (Select All That Apply)
- **UI Render:** Multiple selection checkboxes (A, B, C, D, E, F).
- **User Answer Format:** `Array of Strings` (e.g., `["A", "C", "D"]`)
- **JSON Structure:**
  ```json
  {
      "type": "SATA",
      "question": "Select all that apply. Which symptoms indicate...",
      "options": {
          "A": "Option 1",
          "B": "Option 2",
          "C": "Option 3",
          "D": "Option 4",
          "E": "Option 5"
      },
      "answers": ["A", "C", "E"],
      "explanation": "Explanation text..."
  }
  ```

### 3. `NGN` (Next-Generation Case Study)
- **UI Render:** Top box for Clinical Case Scenario + Question box below with radio buttons.
- **User Answer Format:** `String` (e.g., `"A"`)
- **JSON Structure:**
  ```json
  {
      "type": "NGN",
      "scenario": "A 68-year-old female is admitted with heart failure. VS: BP 90/60, HR 110, RR 28, SpO2 89%. Bilateral crackles, 3+ pitting edema.",
      "question": "Based on the clinical findings, which nursing action should be prioritized?",
      "options": {
          "A": "Apply low-flow oxygen",
          "B": "Place in flat position",
          "C": "Restrict fluids",
          "D": "Obtain blood sample"
      },
      "answer": "A",
      "explanation": "Clinical reasoning explanation..."
  }
  ```

### 4. `FITB` (Fill-in-the-Blank)
- **UI Render:** Text input field.
- **User Answer Format:** `String` (e.g., `"60-100"`)
- **JSON Structure:**
  ```json
  {
      "type": "FITB",
      "question": "The normal adult resting heart rate is ______ beats per minute.",
      "answer": "60-100",
      "explanation": "Normal resting rate is 60 to 100 bpm."
  }
  ```

### 5. `MIX` (Mix and Match)
- Each question in the list will have its own `"type"` field (`MCQ`, `SATA`, `NGN`, or `FITB`). Render dynamically per item!

---

## ✏️ 3. Submit Question Answer (During Exam)

Call this endpoint as the user selects/enters an answer for a question.

- **URL:** `/api/notes_flashcard/nclex/<quiz_id>/submit/`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`

### Request Body Examples

#### Submitting MCQ or NGN Answer:
```json
{
    "question_index": 0,
    "user_answer": "B"
}
```

#### Submitting SATA Answer:
```json
{
    "question_index": 1,
    "user_answer": ["A", "C", "E"]
}
```

#### Submitting FITB Answer:
```json
{
    "question_index": 2,
    "user_answer": "60-100"
}
```

### Response (200 OK)

```json
{
    "question_index": 0,
    "user_answer": "B",
    "is_correct": true,
    "correct_answer": "B",
    "explanation": "Loop diuretics increase potassium excretion, causing hypokalemia.",
    "answered_count": 3,
    "total_questions": 10,
    "correct_count": 2,
    "incorrect_count": 1
}
```

---

## 📊 4. Full Exam Score & Overview (After Exam Finish)

Call this endpoint after the user completes the exam or clicks "Finish Exam / View Results".

- **URL:** `/api/notes_flashcard/nclex/<quiz_id>/score/`
- **Method:** `GET`

### Response (200 OK)

```json
{
    "id": 16,
    "program": "RN",
    "question_format": "MIX",
    "total_questions": 4,
    "answered_count": 4,
    "correct_count": 3,
    "incorrect_count": 1,
    "unanswered_count": 0,
    "score_percentage": 75.0,
    "passed": true,
    "breakdown": [
        {
            "question_index": 0,
            "type": "MCQ",
            "question": "Which electrolyte imbalance is most commonly associated with loop diuretic therapy?",
            "options": {
                "A": "Hypernatremia",
                "B": "Hypokalemia",
                "C": "Hypercalcemia",
                "D": "Hypermagnesemia"
            },
            "scenario": null,
            "user_answer": "B",
            "correct_answer": "B",
            "is_correct": true,
            "is_answered": true,
            "explanation": "Loop diuretics increase potassium excretion."
        },
        {
            "question_index": 1,
            "type": "SATA",
            "question": "Select all that apply. Which interventions are appropriate for pneumonia?",
            "options": {
                "A": "Deep breathing exercises",
                "B": "Antibiotics",
                "C": "Restrict fluids",
                "D": "Monitor SpO2"
            },
            "scenario": null,
            "user_answer": ["A", "B", "D"],
            "correct_answer": ["A", "B", "D"],
            "is_correct": true,
            "is_answered": true,
            "explanation": "Deep breathing and antibiotics are key."
        },
        {
            "question_index": 2,
            "type": "NGN",
            "scenario": "A 72yo COPD patient has SpO2 87% and dyspnea.",
            "question": "Which action should be prioritized?",
            "options": {
                "A": "Apply 1-2 L/min O2 via nasal cannula",
                "B": "Apply high-flow NRB mask",
                "C": "Position flat",
                "D": "Wait for ABG results"
            },
            "user_answer": "B",
            "correct_answer": "A",
            "is_correct": false,
            "is_answered": true,
            "explanation": "Low-flow O2 is indicated to prevent suppression of hypoxic drive."
        },
        {
            "question_index": 3,
            "type": "FITB",
            "question": "The antidote for heparin overdose is ______.",
            "options": null,
            "scenario": null,
            "user_answer": "protamine sulfate",
            "correct_answer": "protamine sulfate",
            "is_correct": true,
            "is_answered": true,
            "explanation": "Protamine sulfate neutralizes heparin."
        }
    ]
}
```

---

## 🔄 5. Restart / Retake Exam

Resets all user progress for a quiz set so the user can retake it from scratch.

- **URL:** `/api/notes_flashcard/nclex/<quiz_id>/restart/`
- **Method:** `POST`

### Response (200 OK)

```json
{
    "message": "Quiz progress reset successfully.",
    "quiz_id": 16,
    "cleared_count": 4
}
```

---

## 📚 6. Quiz History & Details

### List User's Quizzes (Lightweight List)
- **URL:** `/api/notes_flashcard/nclex/`
- **Method:** `GET`
- **Response:**
  ```json
  [
      {
          "id": 16,
          "program": "RN",
          "question_format": "MIX",
          "question_requested": 4,
          "total_questions": 4,
          "file_name": "Manual Content",
          "created_at": "2026-08-15T12:00:00.000000Z"
      }
  ]
  ```

### Get Single Quiz Details (Full Questions)
- **URL:** `/api/notes_flashcard/nclex/<quiz_id>/`
- **Method:** `GET`

---

## 🗑️ 7. Delete Endpoints

### Delete Single Quiz
- **URL:** `/api/notes_flashcard/nclex/<quiz_id>/delete/`
- **Method:** `DELETE`
- **Response:** `{ "message": "Quiz deleted successfully." }`

### Delete All Quizzes
- **URL:** `/api/notes_flashcard/nclex/clear/`
- **Method:** `DELETE`
- **Response:** `{ "message": "All quizzes deleted successfully.", "deleted_count": 10 }`
