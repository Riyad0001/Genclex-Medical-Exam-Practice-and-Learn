from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.nclex.models import CalculatorHistory, Exam, Question, Option, Result, Category
from .serializers import CalculatorSerializer, CalculatorHistory, QuestionSerializer,UserResultSerializer,ExamCompleteSerializer,NextExamSerializer, ExamQuestionSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

# ------------------------------- Calculative APIVIEW -----------------------------------#
class CalculatorAPIView(APIView):
    permission_classes= [IsAuthenticated]
    def post(self, request):
        serializer = CalculatorSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": "failed",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Invalid data",
                "errors": serializer.errors
            })

        action = serializer.validated_data.get("action")

        if action == "clear":
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Calculator cleared",
                "data": {
                    "num1": None,
                    "num2": None,
                    "operation": None,
                    "result": None
                }
            })

        num1 = serializer.validated_data.get("num1")
        num2 = serializer.validated_data.get("num2")
        operation = serializer.validated_data.get("operation")

        if num1 is None or num2 is None or operation is None:
            return Response({
                "status": "failed",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "num1, num2, operation required"
            })

        if operation == "add":
            result = num1 + num2
            expression = f"{int(num1)} + {int(num2)}"

        elif operation == "sub":
            result = num1 - num2
            expression = f"{num1} - {num2}"

        elif operation == "mul":
            result = num1 * num2
            expression = f"{num1} * {num2}"

        elif operation == "div":
            if num2 == 0:
                return Response({
                    "status": "failed",
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "message": "Cannot divide by zero"
                })
            result = num1 // num2
            expression = f"{int(num1)} / {int(num2)}"

        # save history
        history = CalculatorHistory.objects.create(
            user=request.user if request.user.is_authenticated else None,
            num1=num1,
            num2=num2,
            operation=operation,
            expression=expression,
            result=result
        )

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Calculation successful",
            "data": {
                "num1": num1,
                "num2": num2,
                "operation": operation,
                "expression": expression,
                "result": result
            }

        })


# --------------------------------- Exam Question View --------------------------#
class ExamQuestionView(APIView):
    permission_classes= [IsAuthenticated]

    def get(self, request, exam_id):
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({"error": "Exam not found"}, status=404)
        
        questions = Question.objects.filter(exam=exam).order_by('id')[:5]

        serializer = QuestionSerializer(questions, many=True)

        grouped_data = {}
        for q in serializer.data:
            cat = q['category']
            if cat not in grouped_data:
                grouped_data[cat] = []
            grouped_data[cat].append(q)

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Exam questions fetched successfully",
            "data": {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "questions": grouped_data
            }
        })
    

 # --------------------------- Answer Submited -------------------------#
class SubmitExamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        exam_id = request.data.get("exam_id")
        answers = request.data.get("answers", [])

        try:
            exam = Exam.objects.get(id=exam_id, user=user)
        except Exam.DoesNotExist:
            return Response({"error": "Exam not found"}, status=404)

        response_data = []

        for item in answers:
            question_id = item.get("question_id")
            option_ids = item.get("option_id") 
            action = item.get("action")

            try:
                question = Question.objects.get(id=question_id, exam=exam)
            except Question.DoesNotExist:
                continue

            # reset per question state
            question.is_flagged = False
            question.is_skipped = False
            question.save()

            # reset option selection
            Option.objects.filter(question=question).update(is_select=False)

            selected_option = None
            is_correct = False

            # ---------------- ANSWER ----------------
            if action == "answer":

                # MULTIPLE ANSWER
                if isinstance(option_ids, list):

                    if not question.is_multiple:
                        return Response({
                            "error": f"Question {question_id} is single choice only"
                        }, status=422)

                    options = Option.objects.filter(
                        id__in=option_ids,
                        question=question
                    )

                    options.update(is_select=True)

                    selected_option = [o.mcq_option for o in options]
                    is_correct = all(o.is_correct for o in options)

                # SINGLE ANSWER
                else:
                    option = Option.objects.get(
                        id=option_ids,
                        question=question
                    )

                    option.is_select = True
                    option.save()

                    selected_option = option.mcq_option
                    is_correct = option.is_correct

            # ---------------- FLAG ----------------
            elif action == "flag":
                question.is_flagged = True
                question.save()

            # ---------------- SKIP ----------------
            elif action == "skip":
                question.is_skipped = True
                question.save()

            response_data.append({
                "question_id": question.id,
                "question": question.exam_question,
                "selected_option": selected_option,
                "is_correct": is_correct,
                "flagged": question.is_flagged,
                "skipped": question.is_skipped
            })

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Question ans submitted successfully",
            "exam_id": exam.id,
            "total_submitted": len(response_data),
            "results": response_data
        })
    

# ----------------------------- Answer Completed ----------------------------- #
class CompleteExamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        exam_id = request.data.get("exam_id")

        print("REQUEST USER:", user.id)

        try:
            exam = Exam.objects.get(id=exam_id, user=user)
        except Exam.DoesNotExist:
            return Response({"error": "Exam not found"}, status=404)

        print("current exam_id:", exam.exam_id)

        # ---------------- RESULT ----------------
        result = Result.objects.get(user=user, exam=exam)

        total_questions = exam.total_questions or 1
        correct_answers = int(result.correct_ans)

        # ---------------- CALCULATION ----------------
        score = (correct_answers / total_questions) * 100
        mcq_submit = f"{correct_answers}/{total_questions}"

        # ---------------- STATUS RULE ----------------
        if score >= 50:
            exam.completed_exam = True
            exam.status = "completed"
        else:
            exam.completed_exam = False
            exam.status = "incomplete"

        exam.is_lock = True
        exam.submitted_at = timezone.now()
        exam.save()

        # ---------------- NEXT EXAMS ----------------
        next_exam = Exam.objects.filter(user=user, exam_id=exam.exam_id + 1).first()
        next_next_exam = Exam.objects.filter(user=user, exam_id=exam.exam_id + 2).first()

        if next_exam:
            next_exam.status = "up_next"
            next_exam.is_lock = "True" if score >= 50 else "False"
            next_exam.save()

        if next_next_exam:
            next_next_exam.status = "Locked"
            next_next_exam.is_lock = "False"
            next_next_exam.save()

        # ---------------- BUILD FULL RESPONSE LIST ----------------
        all_exams = Exam.objects.filter(user=user).order_by("exam_id")

        response_data = []

        for ex in all_exams:
            res = Result.objects.filter(user=user, exam=ex).first()

            total_q = ex.total_questions or 1
            correct = int(res.correct_ans) if res and res.correct_ans else 0
            incorrect = total_q - correct

            sc = (correct / total_q) * 100
            submitted = Question.objects.filter(
                exam=ex,
                options__is_select=True
            ).distinct().count()    
            mcq_submit = f"{submitted}/{total_q}"

            response_data.append({
                "id": ex.id,
                "title": ex.title,
                "description": ex.description,
                "level": ex.level,
                "exam_duration": ex.exam_duration,
                "total_questions": total_q,

                "correct_answers": correct,
                "incorrect_answer": incorrect,

                "score": sc,
                "mcq_submit": mcq_submit,
                "status": ex.status,
                "is_lock": ex.is_lock,

                "completed_at": res.finished_date if res else None
            })

        # ---------------- FINAL RESPONSE ----------------
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Exam processed successfully",
            "data": response_data
        })


# --------------------------------------- Exam Details View -----------------------------#
class ExamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        user = request.user

        # ---------------- EXAM ----------------
        try:
            exam = Exam.objects.get(id=exam_id, user=user)
        except Exam.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": 404,
                "message": "Exam not found"
            })

        # ---------------- RESULT ----------------
        result = Result.objects.filter(user=user, exam=exam).first()

        total_questions = exam.total_questions or 1

        correct_answers = int(result.correct_ans) if result and result.correct_ans else 0
        incorrect_answers = total_questions - correct_answers

        score = (correct_answers / total_questions) * 100 if total_questions else 0

        flagged = int(result.flag_question) if result and result.flag_question else 0
        skipped = int(result.skip_question) if result and result.skip_question else 0

        # ---------------- CATEGORY DATA (ALL INCLUDE) ----------------
        category_data = []

        for cat in Category.objects.all():

            # ❗ IMPORTANT: all questions of exam category
            questions = Question.objects.filter(
                exam=exam,
                category=cat
            )

            total_q = questions.count()

            if total_q == 0:
                continue

            correct_q = 0

            for q in questions:

                selected_ids = set(
                    q.options.filter(is_select=True).values_list('id', flat=True)
                )

                correct_ids = set(
                    q.options.filter(is_correct=True).values_list('id', flat=True)
                )

                # full match only
                if selected_ids == correct_ids and len(correct_ids) > 0:
                    correct_q += 1

            percentage = (correct_q / total_q) * 100
            print(cat.name, total_q, correct_q)
            category_data.append({
                "category_id": cat.id,
                "category": cat.name,
                "percentage": round(percentage),
                "correct": f"{correct_q}/{total_q}"
            })
        # ---------------- RESPONSE ----------------
        return Response({
            "status": "success",
            "status_code": 200,
            "message": "Exam details fetched successfully",
            "data": {
                "id": exam.id,
                "title": exam.title,
                "total_questions": total_questions,

                "correct_answers": correct_answers,
                "incorrect_answer": incorrect_answers,
                "score": score,

                "status": exam.status,
                "is_lock": exam.is_lock,
                "completed_at": result.finished_date if result else None,
                "category_data": category_data
            }
        })
    

# --------------------------------- Exam Questions Details ----------------------------- #
class ExamQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        user = request.user

        try:
            exam = Exam.objects.get(id=exam_id, user=user)
        except Exam.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Exam not found"
            }, status=404)

        questions = Question.objects.filter(exam=exam).select_related("category").prefetch_related("options")

        data = []

        for q in questions:

            # correct options
            correct_options = q.options.filter(is_correct=True)
            correct_ans = [opt.mcq_option for opt in correct_options]

            # wrong options (user selected but wrong)
            wrong_options = q.options.filter(is_select=True, is_correct=False)
            wrong_ans = [opt.mcq_option for opt in wrong_options]

            data.append({
                "question_id": q.id,
                "category": q.category.name if q.category else None,
                "subcategory": q.subcategory,

                "question": q.exam_question,
                "image": q.explanation_image.url if q.explanation_image else None,
                "explanation": q.explanation,

                "correct_answer": correct_ans,
                "wrong_answer": wrong_ans
            })

        return Response({
            "status": "success",
            "status_code": 200,
            "message": "Exam question details fetched successfully",
            "data": data
        })
    

# --------------------------------- Exam Questions View -------------------------------#
class ExamQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exam_id):
        user = request.user

        try:
            exam = Exam.objects.get(id=exam_id, user=user)
        except Exam.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Exam not found"
            }, status=404)

        questions = Question.objects.filter(
            exam=exam
        ).select_related("category").prefetch_related("options")

        data = []

        for q in questions:

            selected_ids = set(
                q.options.filter(is_select=True).values_list("id", flat=True)
            )

            correct_ids = set(
                q.options.filter(is_correct=True).values_list("id", flat=True)
            )

            is_correct = selected_ids == correct_ids and len(correct_ids) > 0

            data.append({
                "question_id": q.id,
                "category": q.category.name,
                "subcategory": q.subcategory,

                "question": q.exam_question,

                "is_correct": is_correct,

                "explanation": q.explanation,
                "image": q.explanation_image.url if q.explanation_image else None
            })

        serializer = ExamQuestionSerializer(data, many=True)

        return Response({
            "status": "success",
            "status_code": 200,
            "message": "Exam questions fetched successfully",
            "exam_id": exam.id,
            "exam_name": exam.title,
            "data": serializer.data
        })