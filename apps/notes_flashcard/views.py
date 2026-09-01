from requests import request
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI
import os
import json
import re
import PyPDF2
import docx
from PIL import Image
import pytesseract
from apps.notes_flashcard.models import FlashcardSet, FlashcardProgress, NotesQuiz, NotesQuizProgress
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



 # FILE TEXT EXTRACTION# 
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image)


# ------------------------------ flashcard generate --------------------------- #

# POST: GENERATE + SAVE
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_flashcards(request):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # -------------------------
        # Inputs
        # -------------------------
        uploaded_file = request.FILES.get("file")
        content_source = (request.data.get("content_source") or "").strip()
        card_count = int(request.data.get("card_count", 10))
        program = request.data.get("program", "RN")
        if program not in ("LPN", "RN"):
            program = "RN"

        # Clamp card count to a sensible range
        card_count = max(1, min(card_count, 30))

        # -------------------------
        # Get Text
        # -------------------------
        text = ""
        file_name = ""

        if uploaded_file:

            file_name = uploaded_file.name
            extension = uploaded_file.name.lower()

            if extension.endswith(".pdf"):
                text = extract_pdf(uploaded_file)

            elif extension.endswith(".docx"):
                text = extract_docx(uploaded_file)

            elif extension.endswith((".png", ".jpg", ".jpeg")):
                text = extract_image(uploaded_file)

            else:
                return Response(
                    {
                        "message": "Unsupported file format."
                    },
                    status=400,
                )

        elif content_source:

            text = content_source
            file_name = "Manual Content"

        else:
            return Response(
                {
                    "message": "Please upload a file or provide content_source."
                },
                status=400,
            )

        if not text.strip():
            return Response(
                {
                    "message": "No text found."
                },
                status=400,
            )

        # -------------------------
        # Prompt
        # -------------------------
        prompt = f"""You are an expert {program} nursing flashcard generator.

You MUST generate EXACTLY {card_count} flashcards from the content below.

IMPORTANT RULES:
1. Generate EXACTLY {card_count} flashcards — no fewer, no more.
2. Base your flashcards on the provided content.
3. If the content is short, create different angles: definitions, key terms, true/false style, fill-in-the-blank style, clinical application, and "why" questions to reach the required count of {card_count}.
4. Each flashcard must have a "question" and an "answer" field.
5. Return ONLY valid JSON, no markdown, no extra text.

Return this exact JSON structure:

{{
  "flashcards": [
    {{
      "question": "...",
      "answer": "..."
    }}
  ]
}}

You MUST return exactly {card_count} objects in the "flashcards" array.

CONTENT:

{text}"""

        # -------------------------
        # OpenAI
        # -------------------------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=8000,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"You are a flashcard generator. You MUST return valid JSON with EXACTLY {card_count} flashcards. Never return fewer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw_output = response.choices[0].message.content

        print("=" * 80)
        print(raw_output)
        print("=" * 80)

        # -------------------------
        # Parse JSON
        # -------------------------
        try:
            result = json.loads(raw_output)

        except json.JSONDecodeError:

            return Response(
                {
                    "message": "Invalid JSON returned by AI.",
                    "raw_output": raw_output,
                },
                status=500,
            )

        flashcards = result.get("flashcards", [])

        if not isinstance(flashcards, list):

            return Response(
                {
                    "message": "Flashcards should be a list."
                },
                status=500,
            )

        if len(flashcards) == 0:

            return Response(
                {
                    "message": "AI did not generate any flashcards.",
                    "raw_output": raw_output,
                },
                status=500,
            )

        flashcards = flashcards[:card_count]

        # -------------------------
        # Save
        # -------------------------
        flashcard = FlashcardSet.objects.create(
            user=request.user,
            program=program,
            cards_requested=card_count,
            file_name=file_name,
            content_source=content_source,
            flashcards=flashcards,
        )

        # -------------------------
        # Add card_index to each card
        # -------------------------
        cards_with_index = []
        for idx, card in enumerate(flashcard.flashcards):
            c = card.copy()
            c["card_index"] = idx
            cards_with_index.append(c)

        # -------------------------
        # Response
        # -------------------------
        return Response(
            {
                "id": flashcard.id,
                "program": flashcard.program,
                "cards_requested": flashcard.cards_requested,
                "file_name": flashcard.file_name,
                "total_cards": len(cards_with_index),
                "flashcards": cards_with_index,
                "created_at": flashcard.created_at,
            },
            status=201,
        )

    except Exception as e:

        return Response(
            {
                "message": str(e)
            },
            status=500,
        )


# GET SINGLE (with card_index + progress stats)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flashcard(request, pk):
    try:
        obj = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard not found"}, status=404)

    # Add card_index to each card
    cards_with_index = []
    for idx, card in enumerate(obj.flashcards):
        c = card.copy()
        c["card_index"] = idx
        cards_with_index.append(c)

    # Progress stats
    all_progress = FlashcardProgress.objects.filter(flashcard_set=obj)
    know_count = all_progress.filter(know_it=True).count()
    still_learning_count = all_progress.filter(know_it=False).count()
    total = len(obj.flashcards)
    mastered_pct = round((know_count / total * 100), 1) if total > 0 else 0

    return Response({
        "id": obj.id,
        "program": obj.program,
        "cards_requested": obj.cards_requested,
        "file_name": obj.file_name,
        "total_cards": total,
        "know_it_count": know_count,
        "still_learning_count": still_learning_count,
        "mastered_percentage": mastered_pct,
        "flashcards": cards_with_index,
        "created_at": obj.created_at,
    })


# GET LIST (history — lightweight, with progress stats)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_list(request):
    data = FlashcardSet.objects.filter(
        user=request.user
    ).order_by("-created_at")

    result = []
    for obj in data:
        total = len(obj.flashcards) if isinstance(obj.flashcards, list) else 0
        all_progress = FlashcardProgress.objects.filter(flashcard_set=obj)
        know_count = all_progress.filter(know_it=True).count()
        still_learning_count = all_progress.filter(know_it=False).count()
        mastered_pct = round((know_count / total * 100), 1) if total > 0 else 0

        result.append({
            "id": obj.id,
            "program": obj.program,
            "cards_requested": obj.cards_requested,
            "file_name": obj.file_name,
            "total_cards": total,
            "know_it_count": know_count,
            "still_learning_count": still_learning_count,
            "mastered_percentage": mastered_pct,
            "created_at": obj.created_at,
        })

    return Response(result)


# DELETE SINGLE flashcard set
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_flashcard_set(request, pk):
    """
    DELETE /flashcards/<pk>/delete/

    Deletes a single flashcard set and all its progress records.
    """
    try:
        obj = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard set not found."}, status=404)

    obj.delete()
    return Response({"message": "Flashcard set deleted successfully."})


# DELETE ALL flashcard sets for user
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_flashcard_sets(request):
    """
    DELETE /flashcards/clear/

    Deletes all flashcard sets and their progress records for the logged-in user.
    """
    count, _ = FlashcardSet.objects.filter(user=request.user).delete()
    return Response({
        "message": "All flashcard sets deleted successfully.",
        "deleted_count": count,
    })


# -------------------------------- NCLEX_QUIZ -------------------------------------- #

# FILE TEXT EXTRACTION
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image)


# -------------------------------- NCLEX_QUIZ GENERATE -------------------------------------- #


def _get_format_prompt(question_format, question_count):
    """Return format-specific instructions and JSON template for each question type."""

    if question_format == "SATA":
        return f"""
Question Format: SELECT ALL THAT APPLY (SATA)

Rules:
1. Generate EXACTLY {question_count} SATA questions.
2. Each question must have 5-6 options.
3. Multiple options can be correct (at least 2 correct per question).
4. Return the correct answers as a list of letters.

Return this JSON structure:
{{
  "quiz": [
    {{
      "type": "SATA",
      "question": "Select all that apply. Which nursing interventions are appropriate for...",
      "options": {{
        "A": "Option text",
        "B": "Option text",
        "C": "Option text",
        "D": "Option text",
        "E": "Option text"
      }},
      "answers": ["A", "C", "E"],
      "explanation": "Explain why each correct answer is right and each wrong answer is wrong."
    }}
  ]
}}"""

    elif question_format == "NGN":
        return f"""
Question Format: NEXT-GENERATION (NGN) CASE STUDIES

Rules:
1. Generate EXACTLY {question_count} NGN case-based questions.
2. Each question starts with a clinical scenario (2-4 sentences).
3. Then asks a clinical judgment question about the scenario.
4. Each must have exactly 4 options (A, B, C, D) with ONE correct answer.

Return this JSON structure:
{{
  "quiz": [
    {{
      "type": "NGN",
      "scenario": "A 68-year-old female is admitted with heart failure. VS: BP 90/60, HR 110, RR 28, SpO2 89%. Bilateral crackles, 3+ pitting edema.",
      "question": "Based on the clinical findings, which nursing action should be prioritized?",
      "options": {{
        "A": "Option text",
        "B": "Option text",
        "C": "Option text",
        "D": "Option text"
      }},
      "answer": "A",
      "explanation": "Clinical reasoning explanation."
    }}
  ]
}}"""

    elif question_format == "FITB":
        return f"""
Question Format: FILL-IN-THE-BLANK

Rules:
1. Generate EXACTLY {question_count} fill-in-the-blank questions.
2. Each question has a blank indicated by ______.
3. Provide the correct answer as a short text.
4. Include an explanation.

Return this JSON structure:
{{
  "quiz": [
    {{
      "type": "FITB",
      "question": "The normal adult heart rate is ______ beats per minute.",
      "answer": "60-100",
      "explanation": "The normal resting heart rate for adults ranges from 60 to 100 bpm."
    }}
  ]
}}"""

    elif question_format == "MIX":
        return f"""
Question Format: MIX AND MATCH ALL TYPES

Rules:
1. Generate EXACTLY {question_count} questions total.
2. Use a MIX of these types: MCQ, SATA, NGN, FITB.
3. Try to distribute them roughly equally.
4. Each question MUST include a "type" field indicating its format.

For MCQ: {{ "type": "MCQ", "question": "...", "options": {{"A":"...","B":"...","C":"...","D":"..."}}, "answer": "A", "explanation": "..." }}
For SATA: {{ "type": "SATA", "question": "Select all that apply. ...", "options": {{"A":"...","B":"...","C":"...","D":"...","E":"..."}}, "answers": ["A","C"], "explanation": "..." }}
For NGN: {{ "type": "NGN", "scenario": "...", "question": "...", "options": {{"A":"...","B":"...","C":"...","D":"..."}}, "answer": "A", "explanation": "..." }}
For FITB: {{ "type": "FITB", "question": "The normal range is ______.", "answer": "60-100", "explanation": "..." }}

Return this JSON structure:
{{
  "quiz": [ ... all questions here ... ]
}}"""

    else:  # MCQ (default)
        return f"""
Question Format: STANDARD MULTIPLE CHOICE (MCQ)

Rules:
1. Generate EXACTLY {question_count} MCQ questions.
2. Each question must have exactly 4 options (A, B, C, D).
3. Only ONE option is correct.
4. Initially place the correct answer in option A.
5. Options B, C, D must be realistic distractors.

Return this JSON structure:
{{
  "quiz": [
    {{
      "type": "MCQ",
      "question": "Question text",
      "options": {{
        "A": "Correct answer",
        "B": "Wrong answer",
        "C": "Wrong answer",
        "D": "Wrong answer"
      }},
      "answer": "A",
      "explanation": "Explanation why the correct answer is correct."
    }}
  ]
}}"""


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_nclex_quiz(request):
    try:
        # INPUTS
        file = request.FILES.get("file")
        content_source = (request.data.get("content_source") or "").strip()
        question_requested = request.data.get("question_requested", 10)
        question_format = request.data.get("question_format", "MCQ")
        program = request.data.get("program", "RN")

        # Validate
        if question_format not in ("MCQ", "SATA", "NGN", "FITB", "MIX"):
            question_format = "MCQ"
        if program not in ("LPN", "RN"):
            program = "RN"

        if not file and not content_source:
            return Response({"message": "Please upload a file or provide content_source."}, status=400)

        # SAFE INT + CLAMP (1-30)
        try:
            question_count = int(question_requested)
        except (ValueError, TypeError):
            question_count = 10
        question_count = max(1, min(question_count, 30))

        # TEXT EXTRACTION
        if file:
            filename = file.name.lower()
            if filename.endswith(".pdf"):
                text = extract_pdf(file)
            elif filename.endswith(".docx"):
                text = extract_docx(file)
            elif filename.endswith((".jpg", ".jpeg", ".png")):
                text = extract_image(file)
            else:
                return Response({"message": "Unsupported file type."}, status=400)
        else:
            text = content_source

        # FORMAT-SPECIFIC PROMPT
        format_instructions = _get_format_prompt(question_format, question_count)

        exam_label = "NCLEX-PN" if program == "LPN" else "NCLEX-RN"

        prompt = f"""You are an expert {exam_label} exam question generator for {program} nursing students.

Generate EXACTLY {question_count} questions using the provided study material.

{format_instructions}

You MUST return exactly {question_count} questions in the "quiz" array. If the content is short, create varied questions from different angles.

CONTENT:

{text}"""

        # OPENAI CALL
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=8000,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"You generate valid JSON for NCLEX questions. Return exactly {question_count} questions. Never return fewer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        raw_output = response.choices[0].message.content

        # PARSE JSON
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            return Response({"message": "Invalid AI output", "raw": raw_output}, status=500)

        # Extract quiz array
        if isinstance(parsed, dict):
            quiz = parsed.get("quiz", [])
        elif isinstance(parsed, list):
            quiz = parsed
        else:
            return Response({"message": "AI output is not valid"}, status=500)

        if not isinstance(quiz, list) or len(quiz) == 0:
            return Response({"message": "AI did not generate any questions."}, status=500)

        quiz = quiz[:question_count]

        # SHUFFLE MCQ/NGN OPTIONS & ADD INDEX/ID
        import random
        letters_4 = ["A", "B", "C", "D"]

        formatted_quiz = []
        for idx, q in enumerate(quiz):
            q_copy = q.copy() if isinstance(q, dict) else {}
            q_copy["question_index"] = idx
            q_copy["id"] = idx

            q_type = q_copy.get("type", "MCQ")

            if q_type in ("MCQ", "NGN") and "options" in q_copy and "answer" in q_copy:
                correct_text = q_copy["options"].get(q_copy["answer"])
                if correct_text:
                    vals = list(q_copy["options"].values())
                    random.shuffle(vals)
                    new_opts = {l: v for l, v in zip(letters_4, vals)}
                    for l, v in new_opts.items():
                        if v == correct_text:
                            q_copy["answer"] = l
                            break
                    q_copy["options"] = new_opts

            formatted_quiz.append(q_copy)

        # SAVE TO DB
        obj = NotesQuiz.objects.create(
            user=request.user,
            program=program,
            question_format=question_format,
            question_requested=question_count,
            nclex_quiz=formatted_quiz,
            content_file=file if file else None,
            content_source=content_source if content_source else None,
        )

        return Response({
            "id": obj.id,
            "program": obj.program,
            "question_format": obj.question_format,
            "question_requested": obj.question_requested,
            "total_questions": len(formatted_quiz),
            "quiz": formatted_quiz,
            "created_at": obj.created_at,
        }, status=201)

    except Exception as e:
        return Response({"message": str(e)}, status=500)


# -------------------------- Single quiz get --------------------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nclex_quiz(request, pk):
    try:
        obj = NotesQuiz.objects.get(id=pk, user=request.user)
    except NotesQuiz.DoesNotExist:
        return Response({"message": "Quiz not found"}, status=404)

    raw_quiz = obj.nclex_quiz if isinstance(obj.nclex_quiz, list) else []
    formatted_quiz = []
    for idx, q in enumerate(raw_quiz):
        if isinstance(q, dict):
            c = q.copy()
            c["question_index"] = idx
            c["id"] = idx
            formatted_quiz.append(c)
        else:
            formatted_quiz.append(q)

    return Response({
        "id": obj.id,
        "program": obj.program,
        "question_format": obj.question_format,
        "question_requested": obj.question_requested,
        "total_questions": len(formatted_quiz),
        "quiz": formatted_quiz,
        "created_at": obj.created_at,
    })


# -------------------------- List all quizzes (lightweight) ------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_nclex_quiz(request):
    data = NotesQuiz.objects.filter(user=request.user).order_by("-created_at")

    return Response([
        {
            "id": x.id,
            "program": x.program,
            "question_format": x.question_format,
            "question_requested": x.question_requested,
            "total_questions": len(x.nclex_quiz) if isinstance(x.nclex_quiz, list) else 0,
            "file_name": x.content_file.name if x.content_file else "Manual Content",
            "created_at": x.created_at,
        }
        for x in data
    ])


# -------------------------- Delete single quiz ------------------------- #

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_nclex_quiz(request, pk):
    try:
        obj = NotesQuiz.objects.get(id=pk, user=request.user)
    except NotesQuiz.DoesNotExist:
        return Response({"message": "Quiz not found."}, status=404)

    obj.delete()
    return Response({"message": "Quiz deleted successfully."})


# -------------------------- Delete all quizzes ------------------------- #

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_nclex_quizzes(request):
    count, _ = NotesQuiz.objects.filter(user=request.user).delete()
    return Response({
        "message": "All quizzes deleted successfully.",
        "deleted_count": count,
    })


# -------------------------- Answer Check Helper ----------------------- #

def _check_nclex_answer(question, user_answer):
    """
    Evaluates whether the user's answer is correct for the given question.
    Returns tuple: (is_correct: bool, correct_answer)
    """
    q_type = question.get("type", "MCQ")

    if q_type in ("MCQ", "NGN"):
        correct_ans = str(question.get("answer", "")).strip().upper()
        if user_answer is None:
            return False, correct_ans
        user_ans = str(user_answer).strip().upper()
        return (user_ans == correct_ans), correct_ans

    elif q_type == "SATA":
        correct_ans_list = sorted([str(a).strip().upper() for a in question.get("answers", [])])
        if isinstance(user_answer, list):
            user_ans_list = sorted([str(a).strip().upper() for a in user_answer])
        elif isinstance(user_answer, str):
            user_ans_list = sorted([str(a).strip().upper() for a in user_answer.split(",") if a.strip()])
        else:
            user_ans_list = []
        return (user_ans_list == correct_ans_list), correct_ans_list

    elif q_type == "FITB":
        correct_ans = str(question.get("answer", "")).strip()
        if user_answer is None:
            return False, correct_ans
        user_ans = str(user_answer).strip()
        return (user_ans.lower() == correct_ans.lower()), correct_ans

    return False, question.get("answer")


# -------------------------- Submit Question Answer --------------------- #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_nclex_answer(request, pk):
    """
    POST /api/notes_flashcard/nclex/<pk>/submit/
    Body:
    {
        "question_index": 0,
        "user_answer": "B" // or ["A", "C"] for SATA, or "60-100" for FITB
    }
    """
    try:
        quiz_obj = NotesQuiz.objects.get(id=pk, user=request.user)
    except NotesQuiz.DoesNotExist:
        return Response({"message": "Quiz not found."}, status=404)

    question_index = request.data.get("question_index")
    user_answer = request.data.get("user_answer")

    if question_index is None or user_answer is None:
        return Response({"message": "question_index and user_answer are required."}, status=400)

    try:
        question_index = int(question_index)
    except (ValueError, TypeError):
        return Response({"message": "question_index must be an integer."}, status=400)

    quiz_list = quiz_obj.nclex_quiz if isinstance(quiz_obj.nclex_quiz, list) else []
    total_questions = len(quiz_list)

    if question_index < 0 or question_index >= total_questions:
        return Response({"message": f"question_index must be between 0 and {total_questions - 1}."}, status=400)

    question_data = quiz_list[question_index]
    is_correct, correct_ans = _check_nclex_answer(question_data, user_answer)

    progress_obj, _ = NotesQuizProgress.objects.update_or_create(
        quiz=quiz_obj,
        question_index=question_index,
        defaults={
            "user_answer": user_answer,
            "is_correct": is_correct,
        }
    )

    all_progress = NotesQuizProgress.objects.filter(quiz=quiz_obj)
    correct_count = all_progress.filter(is_correct=True).count()
    incorrect_count = all_progress.filter(is_correct=False).count()
    answered_count = all_progress.count()

    return Response({
        "question_index": question_index,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "correct_answer": correct_ans,
        "explanation": question_data.get("explanation", ""),
        "answered_count": answered_count,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
    })


# -------------------------- Quiz Score & Breakdown Overview ------------- #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nclex_quiz_score(request, pk):
    """
    GET /api/notes_flashcard/nclex/<pk>/score/

    Returns full session overview:
    - total_questions, answered_count, correct_count, incorrect_count, unanswered_count, score_percentage, passed
    - breakdown: list of all questions with user answer, correct answer, is_correct status, options, scenario, explanation.
    """
    try:
        quiz_obj = NotesQuiz.objects.get(id=pk, user=request.user)
    except NotesQuiz.DoesNotExist:
        return Response({"message": "Quiz not found."}, status=404)

    quiz_list = quiz_obj.nclex_quiz if isinstance(quiz_obj.nclex_quiz, list) else []
    total_questions = len(quiz_list)

    user_progress = {
        p.question_index: p for p in NotesQuizProgress.objects.filter(quiz=quiz_obj)
    }

    correct_count = 0
    incorrect_count = 0
    answered_count = len(user_progress)
    unanswered_count = total_questions - answered_count

    breakdown = []
    for idx, q_data in enumerate(quiz_list):
        p = user_progress.get(idx)
        is_answered = p is not None
        user_ans = p.user_answer if is_answered else None
        is_correct, correct_ans = _check_nclex_answer(q_data, user_ans)

        if is_answered:
            if is_correct:
                correct_count += 1
            else:
                incorrect_count += 1

        item = {
            "question_index": idx,
            "type": q_data.get("type", "MCQ"),
            "question": q_data.get("question", ""),
            "options": q_data.get("options", None),
            "scenario": q_data.get("scenario", None),
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct if is_answered else None,
            "is_answered": is_answered,
            "explanation": q_data.get("explanation", ""),
        }
        breakdown.append(item)

    score_percentage = round((correct_count / total_questions * 100), 2) if total_questions > 0 else 0.0
    passed = score_percentage >= 75.0

    return Response({
        "id": quiz_obj.id,
        "program": quiz_obj.program,
        "question_format": quiz_obj.question_format,
        "total_questions": total_questions,
        "answered_count": answered_count,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unanswered_count": unanswered_count,
        "score_percentage": score_percentage,
        "passed": passed,
        "breakdown": breakdown,
    })


# -------------------------- Restart Quiz Exam -------------------------- #

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restart_nclex_quiz(request, pk):
    """
    POST /api/notes_flashcard/nclex/<pk>/restart/

    Resets/clears all user progress for this quiz so the user can retake it.
    """
    try:
        quiz_obj = NotesQuiz.objects.get(id=pk, user=request.user)
    except NotesQuiz.DoesNotExist:
        return Response({"message": "Quiz not found."}, status=404)

    deleted_count, _ = NotesQuizProgress.objects.filter(quiz=quiz_obj).delete()

    return Response({
        "message": "Quiz progress reset successfully.",
        "quiz_id": quiz_obj.id,
        "cleared_count": deleted_count,
    })




# ======================== FLASHCARD PROGRESS ======================== #


# POST: Mark a single card as "Know It" or "Still Learning"
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_flashcard(request, pk):
    """
    POST /flashcards/<pk>/mark/
    Body: { "card_index": 0, "know_it": true }

    Creates or updates FlashcardProgress for the given card.
    Returns the updated counts.
    """
    try:
        flashcard_set = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard set not found."}, status=404)

    card_index = request.data.get("card_index")
    know_it = request.data.get("know_it")

    if card_index is None or know_it is None:
        return Response({"message": "card_index and know_it are required."}, status=400)

    try:
        card_index = int(card_index)
    except (ValueError, TypeError):
        return Response({"message": "card_index must be an integer."}, status=400)

    total_cards = len(flashcard_set.flashcards)
    if card_index < 0 or card_index >= total_cards:
        return Response({"message": f"card_index must be between 0 and {total_cards - 1}."}, status=400)

    progress, _ = FlashcardProgress.objects.update_or_create(
        flashcard_set=flashcard_set,
        card_index=card_index,
        defaults={"know_it": bool(know_it)},
    )

    # Return updated counts
    all_progress = FlashcardProgress.objects.filter(flashcard_set=flashcard_set)
    know_count = all_progress.filter(know_it=True).count()
    still_learning_count = all_progress.filter(know_it=False).count()

    return Response({
        "card_index": card_index,
        "know_it": progress.know_it,
        "know_it_count": know_count,
        "still_learning_count": still_learning_count,
        "total_cards": total_cards,
    })


# GET: Session score / summary for a flashcard set
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_score(request, pk):
    """
    GET /flashcards/<pk>/score/

    Returns the session complete summary:
    - total_cards, know_it_count, still_learning_count, mastered_percentage
    - still_learning_indices (card indexes still marked as "Still Learning")
    """
    try:
        flashcard_set = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard set not found."}, status=404)

    total_cards = len(flashcard_set.flashcards)
    all_progress = FlashcardProgress.objects.filter(flashcard_set=flashcard_set)
    know_count = all_progress.filter(know_it=True).count()
    still_learning_count = all_progress.filter(know_it=False).count()
    mastered_pct = round((know_count / total_cards * 100), 1) if total_cards > 0 else 0

    still_learning_indices = list(
        all_progress.filter(know_it=False).values_list("card_index", flat=True)
    )

    return Response({
        "id": flashcard_set.id,
        "program": flashcard_set.program,
        "total_cards": total_cards,
        "know_it_count": know_count,
        "still_learning_count": still_learning_count,
        "mastered_percentage": mastered_pct,
        "still_learning_indices": still_learning_indices,
    })


# GET: Practice only "Still Learning" cards
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def practice_still_learning(request, pk):
    """
    GET /flashcards/<pk>/still-learning/

    Returns only the flashcards that the user marked as "Still Learning".
    Each card includes its original card_index for subsequent mark calls.
    """
    try:
        flashcard_set = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard set not found."}, status=404)

    still_learning_indices = list(
        FlashcardProgress.objects.filter(
            flashcard_set=flashcard_set, know_it=False
        ).values_list("card_index", flat=True)
    )

    all_cards = flashcard_set.flashcards
    still_learning_cards = []
    for idx in still_learning_indices:
        if 0 <= idx < len(all_cards):
            card = all_cards[idx].copy()
            card["card_index"] = idx
            still_learning_cards.append(card)

    return Response({
        "id": flashcard_set.id,
        "program": flashcard_set.program,
        "total_cards": len(all_cards),
        "still_learning_count": len(still_learning_cards),
        "flashcards": still_learning_cards,
    })


# POST: Shuffle & Restart All — resets all progress for the set
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restart_all(request, pk):
    """
    POST /flashcards/<pk>/restart/

    Deletes all FlashcardProgress for this set so the user
    can practice all cards from scratch.
    Returns the full flashcard set with card_index on each card.
    """
    try:
        flashcard_set = FlashcardSet.objects.get(id=pk, user=request.user)
    except FlashcardSet.DoesNotExist:
        return Response({"message": "Flashcard set not found."}, status=404)

    deleted_count, _ = FlashcardProgress.objects.filter(flashcard_set=flashcard_set).delete()

    # Return all cards with card_index
    cards_with_index = []
    for idx, card in enumerate(flashcard_set.flashcards):
        c = card.copy()
        c["card_index"] = idx
        cards_with_index.append(c)

    return Response({
        "id": flashcard_set.id,
        "program": flashcard_set.program,
        "total_cards": len(cards_with_index),
        "progress_reset": deleted_count,
        "flashcards": cards_with_index,
    })

