from django.shortcuts import get_object_or_404
from django.db.models import Count, F, Prefetch
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    NCLEXTopic,
    NCLEXQuestion,
    NCLEXSubtopic,
    PracticeSession,
    PracticeQuestionResult,
    NCLEXExam,
    NCLEXExamResult,
    NCLEXQBank,
    NCLEXCategory,
    Exam_question_result,
    QuestionOption,
)

from .blueprint import generate_exam_questions
from .analytics import build_detailed_analytics, calculate_readiness_level

from .serializers import (
    StartExamSerializer,
    NCLEXQuestionSerializer,
    SubmitAnswerSerializer,
    ExamSerializer,
    NCLEXPracticeListSerializer,
    PracticeSessionSerializer,
    PracticeSessionCreateSerializer,
    NCLEXPracticeExamQuestionSerializer,
    PracticeAnswerSubmitSerializer,
    NCLEXExamItemSerializer,
    NCLEXExamAnswerSubmitSerializer,
    NCLEXExamFlagSerializer,
)


# =========================================================================
# NCLEX FINAL EXAM (5-STAGE SIMULATOR) API VIEWS
# =========================================================================

class NCLEXExamListAPIView(APIView):
    """
    List all 5 NCLEX Final Exams with progressive unlocking,
    user completion status, scores, readiness tiers, remaining timer, and dates.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        exams = NCLEXExam.objects.filter(is_active=True).prefetch_related("questions").order_by("order", "id")
        user_results = {
            res.exam_id: res
            for res in NCLEXExamResult.objects.filter(user=request.user, exam__in=exams)
        }

        user_states = {}
        prev_completed = True
        prev_exam_title = None
        found_first_available = False

        for exam in exams:
            res = user_results.get(exam.id)

            if res and res.status == "completed":
                readiness = res.analytics_data.get("readiness_level") if isinstance(res.analytics_data, dict) else None
                if not readiness and res.score is not None:
                    readiness = calculate_readiness_level(res.score)["level"]

                user_states[exam.id] = {
                    "status": "completed",
                    "is_unlocked": True,
                    "lock_message": None,
                    "score": round(res.score, 1),
                    "readiness_level": readiness,
                    "completed_date": res.completed_at.strftime("%b %-d, %Y") if res.completed_at else None,
                    "session_id": res.id,
                    "remaining_seconds": 0,
                    "current_question_index": res.current_index,
                    "can_start": False,
                    "can_resume": False,
                    "can_review": True,
                    "tag": exam.tag,
                }
                prev_completed = True
                prev_exam_title = exam.title
            elif res and res.status == "in_progress":
                user_states[exam.id] = {
                    "status": "in_progress",
                    "is_unlocked": True,
                    "lock_message": None,
                    "score": None,
                    "readiness_level": None,
                    "completed_date": None,
                    "session_id": res.id,
                    "remaining_seconds": res.get_remaining_seconds(),
                    "current_question_index": res.current_index,
                    "can_start": False,
                    "can_resume": True,
                    "can_review": False,
                    "tag": exam.tag or "In Progress",
                }
                prev_completed = False
                prev_exam_title = exam.title
            else:
                if prev_completed:
                    tag = exam.tag
                    if not tag and not found_first_available and exam.order != 1:
                        tag = "Up next"
                    elif not tag and exam.order == 1:
                        tag = "Start Here"
                    found_first_available = True

                    user_states[exam.id] = {
                        "status": "available",
                        "is_unlocked": True,
                        "lock_message": None,
                        "score": None,
                        "readiness_level": None,
                        "completed_date": None,
                        "session_id": None,
                        "remaining_seconds": exam.time_limit_mins * 60,
                        "current_question_index": 0,
                        "can_start": True,
                        "can_resume": False,
                        "can_review": False,
                        "tag": tag,
                    }
                    prev_completed = False
                    prev_exam_title = exam.title
                else:
                    lock_msg = f"🔒 Complete {prev_exam_title or 'previous exam'} to unlock" if prev_exam_title else "🔒 Complete previous exam to unlock"
                    user_states[exam.id] = {
                        "status": "locked",
                        "is_unlocked": False,
                        "lock_message": lock_msg,
                        "score": None,
                        "readiness_level": None,
                        "completed_date": None,
                        "session_id": None,
                        "remaining_seconds": 0,
                        "current_question_index": 0,
                        "can_start": False,
                        "can_resume": False,
                        "can_review": False,
                        "tag": exam.tag,
                    }
                    prev_completed = False

        serializer = NCLEXExamItemSerializer(
            exams,
            many=True,
            context={"user_states": user_states, "request": request},
        )
        completed_count = sum(1 for s in user_states.values() if s.get("status") == "completed")

        return Response({
            "total_exams": len(exams),
            "completed_exams": completed_count,
            "exams": serializer.data,
        }, status=status.HTTP_200_OK)


class NCLEXExamStartAPIView(APIView):
    """
    Start or resume an NCLEX Final Exam session.
    Generates an 85-question blueprint assessment and locks question IDs to the attempt.
    Enforces single attempt per exam, sequential unlock, and single active exam at a time.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            NCLEXExam.objects.prefetch_related("questions__answers", "questions__topic", "questions__subtopic"),
            pk=exam_id,
            is_active=True,
        )

        # 1. Check if user has already completed this exam (One attempt only)
        existing_result = NCLEXExamResult.objects.select_for_update().filter(
            user=request.user,
            exam=exam,
        ).first()

        if existing_result and existing_result.status == "completed":
            return Response(
                {
                    "message": "You have already completed this exam. Each exam can be taken only once.",
                    "session_id": existing_result.id,
                    "is_completed": True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Check if previous exams are completed (Progressive unlocking)
        if exam.order > 1:
            prev_exams = NCLEXExam.objects.filter(is_active=True, order__lt=exam.order).values_list("id", flat=True)
            completed_prev = NCLEXExamResult.objects.filter(
                user=request.user,
                exam_id__in=prev_exams,
                status="completed",
            ).count()

            if completed_prev < len(prev_exams):
                prev_exam = NCLEXExam.objects.filter(is_active=True, order=exam.order - 1).first()
                prev_name = prev_exam.title if prev_exam else "previous exam"
                return Response(
                    {
                        "message": f"This exam is locked. Please complete {prev_name} first to unlock it.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 3. Check if user has another exam currently in progress
        other_in_progress = NCLEXExamResult.objects.filter(
            user=request.user,
            status="in_progress",
        ).exclude(exam=exam).first()

        if other_in_progress:
            return Response(
                {
                    "message": f"You already have an active exam in progress ('{other_in_progress.exam.title}'). Please finish it before starting another.",
                    "active_session_id": other_in_progress.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Handle Existing In-Progress Attempt vs New Generation
        if existing_result:
            session = existing_result
            # Check timer expiry
            if session.is_time_expired():
                # Auto-finish if time has expired
                finish_view = NCLEXExamFinishAPIView()
                return finish_view.post(request, session_id=session.id)

            assigned_ids = session.assigned_question_ids
            if not assigned_ids:
                assigned_ids = generate_exam_questions(exam, target_count=exam.total_question or 85)
                session.assigned_question_ids = assigned_ids
                session.total_question = len(assigned_ids)
                session.save(update_fields=["assigned_question_ids", "total_question"])
        else:
            assigned_ids = generate_exam_questions(exam, target_count=exam.total_question or 85)
            if not assigned_ids:
                # Fallback to direct pool if blueprint returns empty
                assigned_ids = list(exam.questions.values_list("id", flat=True)[:exam.total_question or 85])

            if not assigned_ids:
                return Response(
                    {"message": "No questions are configured for this exam yet."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            session = NCLEXExamResult.objects.create(
                user=request.user,
                exam=exam,
                status="in_progress",
                total_question=len(assigned_ids),
                assigned_question_ids=assigned_ids,
                is_unlocked=True,
            )

        # 5. Load questions strictly preserving assigned_ids order
        questions_dict = {
            q.id: q
            for q in NCLEXQuestion.objects.filter(id__in=assigned_ids).select_related("topic", "subtopic").prefetch_related(
                Prefetch("answers", queryset=QuestionOption.objects.order_by("order"))
            )
        }
        ordered_questions = [questions_dict[qid] for qid in assigned_ids if qid in questions_dict]

        return Response(
            {
                "message": "Exam started successfully.",
                "session_id": session.id,
                "exam_id": exam.id,
                "title": exam.title,
                "subtitle": exam.subtitle,
                "level": exam.level,
                "time_limit_mins": exam.time_limit_mins,
                "remaining_seconds": session.get_remaining_seconds(),
                "current_question_index": session.current_index,
                "flagged_question_ids": session.flagged_question_ids,
                "total_questions": len(ordered_questions),
                "questions": NCLEXPracticeExamQuestionSerializer(ordered_questions, many=True).data,
            },
            status=status.HTTP_200_OK if existing_result else status.HTTP_201_CREATED,
        )


class NCLEXExamQuestionsAPIView(APIView):
    """
    Retrieve questions and current progress for an active NCLEX Exam session.
    Preserves fixed question order and returns real-time server timer remaining.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            NCLEXExamResult.objects.select_related("exam").filter(user=request.user),
            pk=session_id,
        )

        assigned_ids = session.assigned_question_ids
        if not assigned_ids:
            assigned_ids = list(session.exam.questions.values_list("id", flat=True)[:session.total_question or 85])

        questions_dict = {
            q.id: q
            for q in NCLEXQuestion.objects.filter(id__in=assigned_ids).select_related("topic", "subtopic").prefetch_related(
                Prefetch("answers", queryset=QuestionOption.objects.order_by("order"))
            )
        }
        ordered_questions = [questions_dict[qid] for qid in assigned_ids if qid in questions_dict]

        if not ordered_questions:
            return Response(
                {"message": "No questions found for this exam."},
                status=status.HTTP_404_NOT_FOUND,
            )

        answered_question_ids = list(
            Exam_question_result.objects.filter(
                exam_result=session,
                is_skipped=False,
            ).values_list("question_id", flat=True)
        )

        is_expired = session.is_time_expired() and session.status == "in_progress"

        return Response(
            {
                "session_id": session.id,
                "exam_id": session.exam.id,
                "title": session.exam.title,
                "subtitle": session.exam.subtitle,
                "level": session.exam.level,
                "time_limit_mins": session.exam.time_limit_mins,
                "remaining_seconds": session.get_remaining_seconds(),
                "is_expired": is_expired,
                "current_question_index": session.current_index,
                "total_questions": len(ordered_questions),
                "answered_question_ids": answered_question_ids,
                "answered_count": len(answered_question_ids),
                "flagged_question_ids": session.flagged_question_ids,
                "flagged_count": len(session.flagged_question_ids),
                "is_completed": session.status == "completed",
                "questions": NCLEXPracticeExamQuestionSerializer(ordered_questions, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class NCLEXExamAnswerAPIView(APIView):
    """
    Submit an answer for a question in the NCLEX Final Exam.
    Operates in Test Mode (does not reveal correct answers or explanations during the exam).
    Enforces server-side timer expiration.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = NCLEXExamAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(
            NCLEXExamResult.objects.select_for_update().select_related("exam").filter(user=request.user),
            pk=serializer.validated_data["session_id"],
        )

        if session.status == "completed":
            return Response(
                {"message": "This exam has already been finished and submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check server timer
        if session.is_time_expired():
            finish_view = NCLEXExamFinishAPIView()
            finish_res = finish_view.post(request, session_id=session.id)
            return Response(
                {
                    "message": "Time has expired. Your exam has been automatically submitted.",
                    "is_expired": True,
                    "is_finished": True,
                    "finish_result": finish_res.data,
                },
                status=status.HTTP_200_OK,
            )

        question = get_object_or_404(
            NCLEXQuestion.objects.prefetch_related("answers"),
            pk=serializer.validated_data["question_id"],
        )

        submitted_answer = serializer.validated_data["answer"]
        selected_option = None
        selected_options = []
        selected_text = None
        selected_highlight = []
        extra_data = {}
        is_correct = False

        if question.type == "radio":
            if not isinstance(submitted_answer, list) or len(submitted_answer) != 1:
                return Response(
                    {"message": "Radio answers must contain a list with exactly one option ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                selected_option_id = int(submitted_answer[0])
            except (TypeError, ValueError):
                return Response(
                    {"message": "Radio answers must contain a valid option ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            selected_option = get_object_or_404(question.answers, pk=selected_option_id)
            is_correct = selected_option.is_correct
            extra_data = {"selected_option_id": selected_option.id}

        elif question.type in ("multiple", "highlight"):
            if not isinstance(submitted_answer, list):
                return Response(
                    {"message": "Multiple-select answers must be a list of option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                selected_ids = [int(opt_id) for opt_id in submitted_answer]
            except (TypeError, ValueError):
                return Response(
                    {"message": "Answers must contain valid option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            valid_ids = set(question.answers.values_list("id", flat=True))
            if not set(selected_ids).issubset(valid_ids):
                return Response(
                    {"message": "One or more selected options do not belong to this question."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_ids = set(question.answers.filter(is_correct=True).values_list("id", flat=True))
            is_correct = set(selected_ids) == correct_ids
            selected_options = list(question.answers.filter(id__in=selected_ids))
            if question.type == "highlight":
                selected_highlight = selected_ids
            extra_data = {"selected_option_ids": selected_ids}

        elif question.type == "order":
            if not isinstance(submitted_answer, list):
                return Response(
                    {"message": "Order answers must be a list of option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                submitted_ids = [int(opt_id) for opt_id in submitted_answer]
            except (TypeError, ValueError):
                return Response(
                    {"message": "Order answers must contain valid option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_ids = list(question.answers.order_by("order").values_list("id", flat=True))
            if len(submitted_ids) != len(correct_ids) or set(submitted_ids) != set(correct_ids):
                return Response(
                    {"message": "Submit every option from this question exactly once."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            is_correct = submitted_ids == correct_ids
            selected_options = list(question.answers.filter(id__in=submitted_ids))
            extra_data = {"submitted_order": submitted_ids}

        elif question.type == "input":
            if not isinstance(submitted_answer, str):
                return Response(
                    {"message": "Input answers must be a text value."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_options = question.answers.filter(is_correct=True)
            if not correct_options.exists():
                return Response(
                    {"message": "Input question configuration error: no correct option set."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            selected_text = submitted_answer
            is_correct = submitted_answer.strip().casefold() == correct_options.first().text.strip().casefold()
            extra_data = {"submitted_answer": submitted_answer}

        else:
            return Response(
                {"message": "Unsupported question type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save or update question result
        result, _ = Exam_question_result.objects.update_or_create(
            exam_result=session,
            question=question,
            defaults={
                "user": request.user,
                "exam": session.exam,
                "category": question.category,
                "subtopic": question.subtopic,
                "answer": selected_option,
                "selected_text": selected_text,
                "selected_highlight": selected_highlight,
                "extra_data": extra_data,
                "is_correct": is_correct,
                "is_skipped": False,
            },
        )
        if selected_options:
            result.selected_answer.set(selected_options)

        # Update current index
        curr_idx = serializer.validated_data.get("current_index")
        if curr_idx is not None:
            session.current_index = curr_idx
            session.save(update_fields=["current_index"])

        answered_count = Exam_question_result.objects.filter(
            exam_result=session,
            is_skipped=False,
        ).count()
        total_questions = len(session.assigned_question_ids) if session.assigned_question_ids else session.total_question

        return Response(
            {
                "message": "Answer recorded successfully.",
                "session_id": session.id,
                "question_id": question.id,
                "answered_count": answered_count,
                "total_questions": total_questions,
                "remaining_count": max(0, total_questions - answered_count),
                "remaining_seconds": session.get_remaining_seconds(),
                "is_all_answered": answered_count >= total_questions,
            },
            status=status.HTTP_200_OK,
        )


class NCLEXExamFlagAPIView(APIView):
    """
    Toggle question flagged status for an active NCLEX Exam attempt.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = NCLEXExamFlagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(
            NCLEXExamResult.objects.select_for_update().filter(user=request.user),
            pk=serializer.validated_data["session_id"],
        )

        if session.status == "completed":
            return Response(
                {"message": "Cannot modify flags on a completed exam."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qid = serializer.validated_data["question_id"]
        is_flagged = serializer.validated_data["is_flagged"]

        flagged_list = list(session.flagged_question_ids)
        if is_flagged:
            if qid not in flagged_list:
                flagged_list.append(qid)
        else:
            if qid in flagged_list:
                flagged_list.remove(qid)

        session.flagged_question_ids = flagged_list
        session.save(update_fields=["flagged_question_ids"])

        Exam_question_result.objects.filter(
            exam_result=session,
            question_id=qid,
        ).update(is_flagged=is_flagged)

        return Response(
            {
                "message": "Question flag status updated.",
                "session_id": session.id,
                "question_id": qid,
                "is_flagged": is_flagged,
                "flagged_question_ids": session.flagged_question_ids,
                "flagged_count": len(session.flagged_question_ids),
            },
            status=status.HTTP_200_OK,
        )


class NCLEXExamSummaryAPIView(APIView):
    """
    Pre-submission status review modal summary before final submission:
    Returns count of answered, unanswered, and flagged questions with remaining time.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            NCLEXExamResult.objects.select_related("exam").filter(user=request.user),
            pk=session_id,
        )

        assigned_ids = session.assigned_question_ids
        total_questions = len(assigned_ids) if assigned_ids else session.total_question

        answered_ids = list(
            Exam_question_result.objects.filter(
                exam_result=session,
                is_skipped=False,
            ).values_list("question_id", flat=True)
        )
        unanswered_ids = [qid for qid in assigned_ids if qid not in answered_ids]

        return Response(
            {
                "session_id": session.id,
                "exam_id": session.exam.id,
                "exam_title": session.exam.title,
                "total_questions": total_questions,
                "answered_count": len(answered_ids),
                "unanswered_count": len(unanswered_ids),
                "unanswered_question_ids": unanswered_ids,
                "flagged_count": len(session.flagged_question_ids),
                "flagged_question_ids": session.flagged_question_ids,
                "remaining_seconds": session.get_remaining_seconds(),
                "is_time_expired": session.is_time_expired(),
            },
            status=status.HTTP_200_OK,
        )


class NCLEXExamFinishAPIView(APIView):
    """
    Finish the NCLEX Final Exam session, compute comprehensive post-exam analytics,
    mark as permanently completed, unlock the next exam, and return detailed review.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _options_for_ids(question, option_ids):
        options = {
            opt.id: {"id": opt.id, "text": opt.text}
            for opt in question.answers.all()
        }
        return [options[opt_id] for opt_id in option_ids if opt_id in options]

    def _user_answer(self, result):
        question = result.question
        extra_data = result.extra_data

        if question.type == "radio":
            return {"id": result.answer.id, "text": result.answer.text} if result.answer else None
        if question.type in ("multiple", "highlight", "order"):
            key = "submitted_order" if question.type == "order" else "selected_option_ids"
            return self._options_for_ids(question, extra_data.get(key, []))
        if question.type == "input":
            return {
                "answer": extra_data.get("submitted_answer"),
                "unit": question.metadata.get("unit") if isinstance(question.metadata, dict) else None,
            }
        return None

    def _correct_answer(self, question):
        if question.type == "radio":
            option = question.answers.filter(is_correct=True).first()
            return {"id": option.id, "text": option.text} if option else None
        if question.type in ("multiple", "highlight"):
            return list(question.answers.filter(is_correct=True).values("id", "text"))
        if question.type == "order":
            return list(question.answers.order_by("order").values("id", "text", "order"))
        if question.type == "input":
            option = question.answers.filter(is_correct=True).first()
            return {
                "answer": option.text if option else None,
                "unit": question.metadata.get("unit") if isinstance(question.metadata, dict) else None,
            }
        return None

    @staticmethod
    def _explanation_url(request, question):
        return (
            request.build_absolute_uri(question.explanation.url)
            if question.explanation
            else None
        )

    def _build_result_payload(self, request, session):
        assigned_ids = session.assigned_question_ids
        if assigned_ids:
            questions_dict = {
                q.id: q
                for q in NCLEXQuestion.objects.filter(id__in=assigned_ids).select_related("category", "topic", "subtopic").prefetch_related("answers")
            }
            questions = [questions_dict[qid] for qid in assigned_ids if qid in questions_dict]
        else:
            questions = list(session.exam.questions.select_related("category", "topic", "subtopic").prefetch_related("answers").order_by("id"))

        results_by_question_id = {
            res.question_id: res
            for res in Exam_question_result.objects.filter(exam_result=session)
            .select_related("question", "answer")
            .prefetch_related("question__answers")
        }

        # Run multi-dimensional diagnostics engine
        analytics = build_detailed_analytics(questions, results_by_question_id)

        review = []
        for question in questions:
            res = results_by_question_id.get(question.id)
            meta = question.metadata if isinstance(question.metadata, dict) else {}
            option_explanations = meta.get("option_explanations") or [
                {"id": opt.id, "text": opt.text, "is_correct": opt.is_correct, "rationale": opt.extra_data.get("rationale")}
                for opt in question.answers.all()
            ]

            if res and not res.is_skipped:
                review.append({
                    "question_id": question.id,
                    "title": question.question,
                    "type": question.type,
                    "level": question.level,
                    "client_needs": meta.get("client_needs") or (question.category.title if question.category else None),
                    "cjmm_function": meta.get("cjmm_function"),
                    "body_system": meta.get("body_system") or (question.topic.title if question.topic else None),
                    "topic": question.topic.title if question.topic else None,
                    "subtopic": question.subtopic.title if question.subtopic else None,
                    "user_answer": self._user_answer(res),
                    "correct_answer": self._correct_answer(question),
                    "is_correct": res.is_correct,
                    "is_skipped": False,
                    "is_flagged": res.is_flagged,
                    "rationale_takeaway": meta.get("tip") or meta.get("rationale"),
                    "option_explanations": option_explanations,
                    "explanation": self._explanation_url(request, question),
                })
            else:
                review.append({
                    "question_id": question.id,
                    "title": question.question,
                    "type": question.type,
                    "level": question.level,
                    "client_needs": meta.get("client_needs") or (question.category.title if question.category else None),
                    "cjmm_function": meta.get("cjmm_function"),
                    "body_system": meta.get("body_system") or (question.topic.title if question.topic else None),
                    "topic": question.topic.title if question.topic else None,
                    "subtopic": question.subtopic.title if question.subtopic else None,
                    "user_answer": None,
                    "correct_answer": self._correct_answer(question),
                    "is_correct": False,
                    "is_skipped": True,
                    "is_flagged": res.is_flagged if res else False,
                    "rationale_takeaway": meta.get("tip") or meta.get("rationale"),
                    "option_explanations": option_explanations,
                    "explanation": self._explanation_url(request, question),
                })

        analytics["review"] = review
        return analytics

    @transaction.atomic
    def post(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            NCLEXExamResult.objects.select_for_update().select_related("exam").filter(user=request.user),
            pk=session_id,
        )

        result_payload = self._build_result_payload(request, session)

        session.total_question = result_payload["total_questions"]
        session.total_correct = result_payload["total_correct"]
        session.total_incorrect = result_payload["total_incorrect"]
        session.total_skipped = result_payload["total_skipped"]
        session.score = result_payload["overall_score"]
        session.analytics_data = result_payload
        if session.status != "completed":
            session.status = "completed"
            session.completed_at = timezone.now()
        session.save(
            update_fields=[
                "total_question",
                "total_correct",
                "total_incorrect",
                "total_skipped",
                "score",
                "analytics_data",
                "status",
                "completed_at",
            ]
        )

        # Check if next exam is now unlocked
        next_exam = NCLEXExam.objects.filter(is_active=True, order=session.exam.order + 1).first()

        return Response(
            {
                "message": "NCLEX Exam finished successfully.",
                "session_id": session.id,
                "exam_id": session.exam.id,
                "exam_title": session.exam.title,
                "is_completed": True,
                "score": session.score,
                "readiness_level": result_payload.get("readiness_level"),
                "readiness_description": result_payload.get("readiness_description"),
                "completed_at": session.completed_at.strftime("%b %-d, %Y") if session.completed_at else None,
                "next_exam_unlocked": next_exam is not None,
                "next_exam_id": next_exam.id if next_exam else None,
                "next_exam_title": next_exam.title if next_exam else None,
                "result": result_payload,
            },
            status=status.HTTP_200_OK,
        )


class NCLEXExamReviewAPIView(NCLEXExamFinishAPIView):
    """
    Retrieve full review and result summary for a completed NCLEX Final Exam session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            NCLEXExamResult.objects.select_related("exam").filter(user=request.user),
            pk=session_id,
        )

        if session.status != "completed":
            return Response(
                {"message": "This exam has not been completed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if session.analytics_data and "review" in session.analytics_data:
            result_payload = session.analytics_data
        else:
            result_payload = self._build_result_payload(request, session)
            session.analytics_data = result_payload
            session.save(update_fields=["analytics_data"])

        return Response(
            {
                "session_id": session.id,
                "exam_id": session.exam.id,
                "exam_title": session.exam.title,
                "exam_subtitle": session.exam.subtitle,
                "level": session.exam.level,
                "score": session.score,
                "readiness_level": result_payload.get("readiness_level"),
                "completed_at": session.completed_at.strftime("%b %-d, %Y") if session.completed_at else None,
                "result": result_payload,
            },
            status=status.HTTP_200_OK,
        )



'''BADSHA - UPDATED API FOR NCLEX EXAM'''
class NCLEXPracticeAPIView(APIView):
    """API view to retrieve NCLEX practice list with nested category, topic, and subtopic summary."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        subtopics = NCLEXSubtopic.objects.annotate(
            total_question=Count("questions", distinct=True)
        ).order_by("title")
        topics = NCLEXTopic.objects.annotate(
            total_subtopic=Count("subtopics", distinct=True)
        ).prefetch_related(
            Prefetch("subtopics", queryset=subtopics)
        ).order_by("title")
        categories = NCLEXCategory.objects.annotate(
            total_question=Count("questions", distinct=True),
            total_topic=Count("topics", distinct=True),
        ).prefetch_related(
            Prefetch("topics", queryset=topics)
        ).order_by("title")

        return Response(NCLEXPracticeListSerializer(categories, many=True).data)


class NCLEXPracticeSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = PracticeSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mode = serializer.validated_data["mode"]
        requested_count = serializer.validated_data["total_question"]
        topic_id = serializer.validated_data.get("topic_id")
        subtopic_id = serializer.validated_data.get("subtopic_id")

        topic = None
        subtopic = None
        if subtopic_id is not None:
            subtopic = get_object_or_404(
                NCLEXSubtopic.objects.select_related("topic"),
                pk=subtopic_id,
            )
            # Keep the parent topic on the session for easier reporting.
            topic = subtopic.topic
            questions = NCLEXQuestion.objects.filter(subtopic=subtopic)
        else:
            topic = get_object_or_404(NCLEXTopic, pk=topic_id)
            questions = NCLEXQuestion.objects.filter(topic=topic)

        available_count = questions.count()
        if requested_count > available_count:
            return Response(
                {
                    "message": (
                        f"Only {available_count} questions are available for the "
                        "selected practice area."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        selected_questions = list(questions.order_by("?")[:requested_count])
        session = PracticeSession.objects.create(
            user=request.user,
            practice_mode=mode,
            total_question=len(selected_questions),
            topic=topic,
            subtopic=subtopic,
        )
        session.question_set.set(selected_questions)

        return Response(
            {
                "session_id": session.id,
                "message": "Practice session created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class NCLEXPracticeExamAPIVieiw(APIView):
    """Return all questions assigned to the authenticated user's practice session."""

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            PracticeSession.objects.filter(user=request.user),
            pk=session_id,
        )
        questions = session.question_set.select_related(
            "topic",
            "subtopic",
        ).prefetch_related(
            Prefetch(
                "answers",
                queryset=QuestionOption.objects.order_by("order"),
            )
        )

        questions = questions.order_by("id")

        if not questions.exists():
            return Response(
                {"message": "No questions are available for this practice session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "session_id": session.id,
                "mode": session.practice_mode,
                "questions": NCLEXPracticeExamQuestionSerializer(
                    questions,
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class NCLEXPracticeAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _options_for_ids(question, option_ids):
        options = {
            option.id: {"id": option.id, "text": option.text}
            for option in question.answers.all()
        }
        return [options[option_id] for option_id in option_ids if option_id in options]

    def _user_answer(self, result):
        question = result.question
        extra_data = result.extra_data

        if question.type == "radio":
            return (
                {"id": result.answer.id, "text": result.answer.text}
                if result.answer
                else None
            )
        if question.type in ("multiple", "highlight", "order"):
            key = "submitted_order" if question.type == "order" else "selected_option_ids"
            return self._options_for_ids(question, extra_data.get(key, []))
        if question.type == "input":
            return {
                "answer": extra_data.get("submitted_answer"),
                "unit": question.metadata.get("unit"),
            }
        return None

    def _correct_answer(self, question):
        if question.type == "radio":
            option = question.answers.filter(is_correct=True).first()
            return {"id": option.id, "text": option.text} if option else None
        if question.type in ("multiple", "highlight"):
            return list(question.answers.filter(is_correct=True).values("id", "text"))
        if question.type == "order":
            return list(question.answers.order_by("order").values("id", "text", "order"))
        if question.type == "input":
            option = question.answers.filter(is_correct=True).first()
            return {
                "answer": option.text if option else None,
                "unit": question.metadata.get("unit"),
            }
        return None

    @staticmethod
    def _explanation_url(request, question):
        return (
            request.build_absolute_uri(question.explanation.url)
            if question.explanation
            else None
        )

    def _review_item(self, request, result):
        return {
            "question_id": result.question_id,
            "title": result.question.question,
            "type": result.question.type,
            "user_answer": self._user_answer(result),
            "correct_answer": self._correct_answer(result.question),
            "is_correct": result.is_correct,
            "explanation": self._explanation_url(request, result.question),
        }

    def _skipped_review_item(self, request, question):
        """Build a review row for a question the user did not answer."""
        return {
            "question_id": question.id,
            "title": question.question,
            "type": question.type,
            "user_answer": None,
            "correct_answer": self._correct_answer(question),
            "is_correct": False,
            "is_skipped": True,
            "explanation": self._explanation_url(request, question),
        }

    def _result_payload(self, request, session):
        """Return an authoritative summary from the saved answer records."""
        questions = list(
            session.question_set.prefetch_related("answers").order_by("id")
        )
        results_by_question_id = {
            result.question_id: result
            for result in session.question_results.select_related("question", "answer")
            .prefetch_related("question__answers")
        }
        answered_results = list(results_by_question_id.values())
        total_correct = sum(result.is_correct for result in answered_results)
        total_incorrect = sum(not result.is_correct for result in answered_results)
        total_skipped = len(questions) - len(answered_results)
        total_question = len(questions)

        review = []
        for question in questions:
            result = results_by_question_id.get(question.id)
            if result:
                item = self._review_item(request, result)
                item["is_skipped"] = False
            else:
                item = self._skipped_review_item(request, question)
            review.append(item)

        return {
            "total_correct_answer": total_correct,
            "total_incorrect_answer": total_incorrect,
            "total_skipped_answer": total_skipped,
            "total_question": total_question,
            "total_percentage": round((total_correct / total_question) * 100, 2)
            if total_question
            else 0,
            "results": review,
        }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = PracticeAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(
            PracticeSession.objects.select_for_update().filter(user=request.user),
            pk=serializer.validated_data["session_id"],
        )
        if session.is_finished:
            return Response(
                {"message": "This practice session has already been finished."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        question = get_object_or_404(
            session.question_set.prefetch_related("answers"),
            pk=serializer.validated_data["question_id"],
        )

        if PracticeQuestionResult.objects.filter(
            session=session,
            question=question,
        ).exists():
            return Response(
                {"message": "An answer for this question has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submitted_answer = serializer.validated_data["answer"]
        selected_option = None
        extra_data = {}

        if question.type == "radio":
            if len(submitted_answer) != 1:
                return Response(
                    {"message": "Radio answers must contain exactly one option ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                selected_option_id = int(submitted_answer[0])
            except (TypeError, ValueError):
                return Response(
                    {"message": "Radio answers must contain a valid option ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            selected_option = get_object_or_404(
                question.answers,
                pk=selected_option_id,
            )
            is_correct = selected_option.is_correct
            extra_data = {"selected_option_id": selected_option.id}

        elif question.type in ("multiple", "highlight"):
            if not isinstance(submitted_answer, list):
                return Response(
                    {"message": "Multiple-select and highlight answers must be lists of option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                selected_ids = [int(option_id) for option_id in submitted_answer]
            except (TypeError, ValueError):
                return Response(
                    {"message": "Answers must contain valid option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            valid_ids = set(question.answers.values_list("id", flat=True))
            if len(selected_ids) != len(set(selected_ids)) or not set(selected_ids).issubset(valid_ids):
                return Response(
                    {"message": "One or more selected options do not belong to this question."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_ids = set(
                question.answers.filter(is_correct=True).values_list("id", flat=True)
            )
            is_correct = set(selected_ids) == correct_ids
            extra_data = {"selected_option_ids": selected_ids}

        elif question.type == "order":
            if not isinstance(submitted_answer, list):
                return Response(
                    {"message": "Order answers must be a list of option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                submitted_ids = [int(option_id) for option_id in submitted_answer]
            except (TypeError, ValueError):
                return Response(
                    {"message": "Order answers must contain valid option IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_ids = list(
                question.answers.order_by("order").values_list("id", flat=True)
            )
            if len(submitted_ids) != len(correct_ids) or set(submitted_ids) != set(correct_ids):
                return Response(
                    {"message": "Submit every option from this question exactly once."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            is_correct = submitted_ids == correct_ids
            extra_data = {"submitted_order": submitted_ids}

        elif question.type == "input":
            if not isinstance(submitted_answer, str):
                return Response(
                    {"message": "Input answers must be a text value."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            correct_options = question.answers.filter(is_correct=True)
            if correct_options.count() != 1:
                return Response(
                    {"message": "This input question must have exactly one correct option."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            submitted_value = submitted_answer
            is_correct = (
                submitted_value.strip().casefold()
                == correct_options.first().text.strip().casefold()
            )
            extra_data = {
                "submitted_answer": submitted_value,
            }

        else:
            return Response(
                {"message": "Unsupported question type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PracticeQuestionResult.objects.create(
            session=session,
            question=question,
            answer=selected_option,
            is_correct=is_correct,
            extra_data=extra_data,
        )
        result_field = "total_correct" if is_correct else "total_incorrect"
        PracticeSession.objects.filter(pk=session.pk).update(**{result_field: F(result_field) + 1})
        session.refresh_from_db(
            fields=["total_question", "total_correct", "total_incorrect", "total_skipped"]
        )

        answered_count = session.question_results.count()
        is_finished = answered_count + session.total_skipped >= session.total_question
        response = {
            "message": "Answer submitted successfully.",
            "session_id": session.id,
            "answer_submitted": True,
            "is_finished": is_finished,
        }

        if session.practice_mode == "tutorial":
            response.update(
                {
                    "is_correct": is_correct,
                    "correct_answer": self._correct_answer(question),
                    "explanation": self._explanation_url(request, question),
                }
            )

        if is_finished:
            response["result"] = self._result_payload(request, session)

        return Response(response, status=status.HTTP_200_OK)


class NCLEXPracticeFinishAPIView(NCLEXPracticeAnswerAPIView):
    """Finish a practice session and return its complete results and review."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            PracticeSession.objects.select_for_update().filter(user=request.user),
            pk=session_id,
        )

        result = self._result_payload(request, session)
        # Persist the summary so session lists and any later reporting remain accurate.
        session.total_question = result["total_question"]
        session.total_correct = result["total_correct_answer"]
        session.total_incorrect = result["total_incorrect_answer"]
        session.total_skipped = result["total_skipped_answer"]
        if not session.is_finished:
            session.is_finished = True
            session.finished_at = timezone.now()
        session.save(
            update_fields=[
                "total_question",
                "total_correct",
                "total_incorrect",
                "total_skipped",
                "is_finished",
                "finished_at",
            ]
        )

        return Response(
            {
                "message": "Practice session finished successfully.",
                "session_id": session.id,
                "is_finished": True,
                "result": result,
            },
            status=status.HTTP_200_OK,
        )

"""BADSHA - UPDATED API FOR NCLEX EXAM"""


# class NCLEXTopicAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         queryset = NCLEXTopic.objects.select_related("category").prefetch_related(
#             "subtopics",
#             "subtopics__questions",
#         )
#         data = []

#         for topic in queryset:
#             category = topic.category
#             category_total_question = category.questions.count()
#             category_total_topic = category.topics.count()
#             topic_total_question = 0
#             subtopic_list = []

#             for subtopic in topic.subtopics.all():
#                 question_list = []

#                 for question in subtopic.questions.all():
#                     question_list.append({})
#                 subtopic_total_question = len(question_list)
#                 topic_total_question += subtopic_total_question

#                 subtopic_list.append(
#                     {
#                         "id": subtopic.id,
#                         "title": subtopic.title,
#                         "total_question": subtopic_total_question,
#                     }
#                 )

#             data.append(
#                 {
#                     "category": {
#                         "id": category.id,
#                         "title": category.title,
#                         "total_question": category_total_question,
#                         "topic": [
#                             {
#                                 "id": topic.id,
#                                 "title": topic.title,
#                                 "subtopics": subtopic_list,
#                             }
#                         ],
#                     },
#                     "total_topic": category_total_topic,
#                     "total_subtopic": topic.subtopics.count(),
#                     "total_category_question": topic_total_question,
#                     "total_subcategory_question": topic_total_question,
#                 }
#             )

#         return Response(
#             {
#                 "data": data,
#                 "message": "Topic list retrieved successfully.",
#             }
#         )


# # ---------------------------- Topic Details --------------------------- #
# class NCLEXTopicDetailsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk):
#         try:
#             category = NCLEXCategory.objects.prefetch_related(
#                 "topics",
#                 "topics__subtopics",
#                 "topics__subtopics__questions",
#             ).get(pk=pk)
#         except NCLEXCategory.DoesNotExist:
#             return Response(
#                 {"success": False, "message": "Category not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         topics_data = []
#         for topic in category.topics.all():

#             subtopics_data = []
#             for subtopic in topic.subtopics.all():

#                 questions = []
#                 for question in subtopic.questions.all():
#                     questions.append(
#                         {
#                             "id": question.id,
#                             "question": question.question,
#                             "type": question.type,
#                             "level": question.level,
#                             "note": question.note,
#                             "avg_solve_percent": question.avg_solve_percent,
#                             "explanation": (
#                                 request.build_absolute_uri(question.explanation.url)
#                                 if question.explanation
#                                 else None
#                             ),
#                         }
#                     )

#                 subtopics_data.append(
#                     {
#                         "id": subtopic.id,
#                         "title": subtopic.title,
#                         "description": subtopic.description,
#                         "total_question": len(questions),
#                         "questions": questions,
#                     }
#                 )

#             topics_data.append(
#                 {
#                     "id": topic.id,
#                     "title": topic.title,
#                     "total_subtopic": topic.subtopics.count(),
#                     "subtopics": subtopics_data,
#                 }
#             )

#         return Response(
#             {
#                 # "success": True,
#                 "data": {
#                     "id": category.id,
#                     "title": category.title,
#                     "total_topic": category.topics.count(),
#                     "total_question": category.questions.count(),
#                     "topics": topics_data,
#                 }
#             }
#         )


# # ---------------------------- Subtopic Details --------------------------- #


# class SubtopicDetailsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk=None):
#         queryset = NCLEXSubtopic.objects.select_related("topic").prefetch_related(
#             "questions",
#         )
#         if pk:
#             try:
#                 subtopic = queryset.get(pk=pk)
#                 queryset = [subtopic]
#             except NCLEXSubtopic.DoesNotExist:
#                 return Response(
#                     {"success": False, "message": "Subtopic not found."},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#         data = []
#         for subtopic in queryset:
#             questions = subtopic.questions.all()
#             question_list = []
#             for question in questions:
#                 question_list.append(
#                     {
#                         "id": question.id,
#                         "question": question.question,
#                         "type": question.type,
#                         "level": question.level,
#                         "note": question.note,
#                         "avg_solve_percent": question.avg_solve_percent,
#                         "explanation": (
#                             request.build_absolute_uri(question.explanation.url)
#                             if question.explanation
#                             else None
#                         ),
#                     }
#                 )
#             data.append(
#                 {
#                     "id": subtopic.id,
#                     "title": subtopic.title,
#                     "total_question": len(question_list),
#                     "questions": question_list,
#                 }
#             )
#         return Response(
#             {
#                 "data": data[0] if pk else data,
#             },
#             status=status.HTTP_200_OK,
#         )


# # ---------------------- Start Exam -----------------------------#
# class StartExamAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = StartExamSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         category_id = serializer.validated_data.get("category_id")
#         subcategory_id = serializer.validated_data.get("subcategory_id")
#         mode = serializer.validated_data.get("mode")
#         question_select = serializer.validated_data.get("question_select")

#         # Category / Subcategory
#         if category_id:
#             category = get_object_or_404(NCLEXCategory, pk=category_id)

#             queryset = (
#                 NCLEXQuestion.objects.filter(category=category)
#                 .prefetch_related("answers")
#                 .order_by("id")
#             )

#             title = category.title

#         else:
#             subcategory = get_object_or_404(NCLEXSubtopic, pk=subcategory_id)

#             queryset = (
#                 NCLEXQuestion.objects.filter(subtopic=subcategory)
#                 .prefetch_related("answers")
#                 .order_by("id")
#             )

#             title = subcategory.title

#         # Total Available Questions
#         available_questions = queryset.count()

#         if available_questions == 0:
#             return Response(
#                 {"status": False, "message": "No questions found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         if question_select > available_questions:
#             return Response(
#                 {
#                     "status": False,
#                     "message": f"Only {available_questions} questions are available.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Random Questions
#         questions = queryset.order_by("?")[:question_select]
#         selected_questions = questions.count()
#         total_time = selected_questions * 60

#         # Create Exam
#         exam = NCLEXQBank.objects.create(
#             nclex=request.user,
#             exam_level="foundational",
#             exam_status="start Here",
#             title=title,
#             subtitle=f"{mode.title()} Mode",
#             total_questions=selected_questions,
#             total_time=total_time,
#         )

#         exam.question_ids.set(questions)

#         # Create Session
#         session = Exam_session.objects.create(
#             user=request.user,
#             exam=exam,
#             total_question=selected_questions,
#             total_time=total_time,
#             exam_type=mode,
#         )

#         # Serialize Questions
#         question_serializer = NCLEXQuestionSerializer(
#             questions,
#             many=True,
#             context={
#                 "request": request,
#                 "mode": mode,
#             },
#         )

#         # Response
#         return Response(
#             {
#                 # "status": True,
#                 "message": "Exam started successfully.",
#                 "exam_id": exam.id,
#                 "session_id": session.id,
#                 "mode": mode,
#                 "category_id": category_id,
#                 "subcategory_id": subcategory_id,
#                 "selected_questions": selected_questions,
#                 "total_questions": available_questions,
#                 "total_time": total_time,
#                 "questions": question_serializer.data,
#             },
#             status=status.HTTP_201_CREATED,
#         )


# # ---------------------- Submit Answer -----------------------------#
# class SubmitAnswerAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = SubmitAnswerSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         exam_id = serializer.validated_data["exam_id"]
#         question_id = serializer.validated_data["question_id"]
#         answer = serializer.validated_data["answer"]
#         exam = get_object_or_404(NCLEXQBank, id=exam_id, nclex=request.user)
#         session = (
#             Exam_session.objects.filter(exam=exam, user=request.user)
#             .order_by("-created_at")
#             .first()
#         )

#         if not session:
#             return Response(
#                 {"status": "error", "message": "Exam session not found."},
#                 status=status.HTTP_404_NOT_FOUND,
#             )

#         question = get_object_or_404(NCLEXQuestion, id=question_id)

#         if not exam.question_ids.filter(id=question.id).exists():
#             return Response(
#                 {
#                     "status": "error",
#                     "status_code": 400,
#                     "message": "This question does not belong to this exam.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Prevent duplicate submit
#         if exam_question_result.objects.filter(
#             session=session, question=question
#         ).exists():
#             return Response(
#                 {
#                     "status": "error",
#                     "status_code": 400,
#                     "message": "Answer already submitted.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         is_correct = False
#         selected_answers = []

#         # Radio
#         if question.type == "radio":

#             correct = question.answers.filter(correct_answer=True).first()
#             is_correct = correct is not None and correct.id == answer
#             selected_answers = Nclex_answer.objects.filter(id=answer, question=question)

#         # Multiple
#         elif question.type == "multiple":

#             correct_ids = set(
#                 question.answers.filter(correct_answer=True).values_list(
#                     "id", flat=True
#                 )
#             )
#             user_ids = set(answer)
#             is_correct = correct_ids == user_ids

#             selected_answers = Nclex_answer.objects.filter(
#                 id__in=answer, question=question
#             )

#         # Drag Order
#         elif question.type == "order":

#             correct = list(
#                 question.answers.order_by("order").values_list("id", flat=True)
#             )
#             is_correct = correct == answer
#             selected_answers = Nclex_answer.objects.filter(
#                 id__in=answer, question=question
#             )

#         # Input
#         elif question.type == "input":
#             accepted_answers = question.metadata.get("accepted_answers", [])
#             user_answer = str(answer)

#             if question.metadata.get("trim_whitespace", True):
#                 user_answer = user_answer.strip()

#             if not question.metadata.get("case_sensitive", False):
#                 user_answer = user_answer.lower()
#                 accepted_answers = [str(x).strip().lower() for x in accepted_answers]
#             else:
#                 accepted_answers = [str(x).strip() for x in accepted_answers]

#             is_correct = user_answer in accepted_answers

#         # Highlight
#         elif question.type == "highlight":

#             correct = set(
#                 question.answers.filter(correct_answer=True).values_list(
#                     "title", flat=True
#                 )
#             )

#             user = set(answer)
#             is_correct = correct == user

#         else:
#             return Response(
#                 {
#                     "status": "error",
#                     "status_code": 400,
#                     "message": "Invalid question type.",
#                 },
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Save Result
#         result = exam_question_result.objects.create(
#             user=request.user,
#             exam=exam,
#             category=question.category,
#             subtopic=question.subtopic,
#             session=session,
#             question=question,
#             is_correct=is_correct,
#             is_skipped=False,
#         )

#         # Save user's answer

#         if question.type in ["radio", "multiple", "order"]:
#             result.selected_answer.set(selected_answers)

#         elif question.type == "input":
#             result.selected_text = answer
#             result.save(update_fields=["selected_text"])

#         elif question.type == "highlight":
#             result.selected_highlight = answer
#             result.save(update_fields=["selected_highlight"])

#         # Progress
#         answered = exam_question_result.objects.filter(session=session).count()

#         remaining = session.total_question - answered

#         response = {
#             # "status": "success",
#             # "status_code": 200,
#             "message": "Answer submitted successfully.",
#             "data": {
#                 "question_id": question.id,
#                 "question_type": question.type,
#                 "is_correct": is_correct,
#                 "answered": answered,
#                 "remaining": remaining,
#             },
#         }

#         # Tutorial Mode
#         if session.exam_type == "tutorial":
#             response["data"]["explanation"] = (
#                 request.build_absolute_uri(question.explanation.url)
#                 if question.explanation
#                 else None
#             )

#         # Test Mode (Show Result After Last Question)
#         if session.exam_type == "test" and remaining == 0:

#             correct = exam_question_result.objects.filter(
#                 session=session, is_correct=True
#             ).count()

#             incorrect = exam_question_result.objects.filter(
#                 session=session, is_correct=False, is_skipped=False
#             ).count()

#             skipped = exam_question_result.objects.filter(
#                 session=session, is_skipped=True
#             ).count()

#             explanations = []

#             results = (
#                 exam_question_result.objects.filter(session=session)
#                 .select_related("question")
#                 .prefetch_related("selected_answer")
#             )

#             for item in results:

#                 # Correct answers
#                 correct_answers = list(
#                     item.question.answers.filter(correct_answer=True).values(
#                         "id", "title", "order"
#                     )
#                 )

#                 # User selected answer
#                 if item.question.type in ["radio", "multiple", "order"]:

#                     selected = list(
#                         item.selected_answer.all().values("id", "title", "order")
#                     )

#                 elif item.question.type == "input":

#                     selected = item.selected_text

#                 elif item.question.type == "highlight":

#                     selected = item.selected_highlight

#                 else:

#                     selected = None

#                 explanations.append(
#                     {
#                         "question_id": item.question.id,
#                         "question": item.question.question,
#                         "question_type": item.question.type,
#                         "selected_answer": selected,
#                         "correct_answer": correct_answers,
#                         "is_correct": item.is_correct,
#                         "explanation": (
#                             request.build_absolute_uri(item.question.explanation.url)
#                             if item.question.explanation
#                             else None
#                         ),
#                     }
#                 )

#             response["data"]["result"] = {
#                 "total_question": session.total_question,
#                 "correct": correct,
#                 "incorrect": incorrect,
#                 "skipped": skipped,
#                 "score": round((correct / session.total_question) * 100, 2),
#                 "review": explanations,
#             }

#         return Response(response, status=status.HTTP_200_OK)


# # ---------------------- Exam List -----------------------------#
# class ExamAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk=None):

#         queryset = (
#             NCLEXQBank.objects.filter(nclex=request.user)
#             .prefetch_related(
#                 "exam_sessions",
#                 "exam_sessions__question_results",
#             )
#             .order_by("-created_at")
#         )

#         if pk:
#             exam = get_object_or_404(queryset, pk=pk)
#             serializer = ExamSerializer(exam)

#             return Response(
#                 {
#                     "status": "success",
#                     "status_code": status.HTTP_200_OK,
#                     "message": "Exam retrieved successfully.",
#                     "data": serializer.data,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         serializer = ExamSerializer(queryset, many=True)
#         return Response(
#             {
#                 # "status": "success",
#                 # "status_code": status.HTTP_200_OK,
#                 "message": "Exam list retrieved successfully.",
#                 "data": serializer.data,
#             },
#             # status=status.HTTP_200_OK,
#         )
