


# Create your views here.
# class CompleteExamView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         exam_id = request.data.get("exam_id")

#         print("REQUEST USER:", user.id)

#         try:
#             exam = Exam.objects.get(id=exam_id, user=user)
#         except Exam.DoesNotExist:
#             return Response({"error": "Exam not found"}, status=404)

#         print("current exam_id:", exam.exam_id)

#         # ---------------- RESULT ----------------
#         result = Result.objects.get(user=user, exam=exam)

#         total_questions = exam.total_questions or 1
#         correct_answers = int(result.correct_ans)  # ✅ admin editable value

#         # ---------------- CALCULATION ----------------
#         score = (correct_answers / total_questions) * 100
#         mcq_submit = f"{correct_answers}/{total_questions}"

#         # ---------------- STATUS RULE ----------------
#         if score >= 50:
#             exam.completed_exam = True
#             exam.status = "completed"
#         else:
#             exam.completed_exam = False
#             exam.status = "incomplete"

#         exam.is_lock = True
#         exam.submitted_at = timezone.now()
#         exam.save()

#         # ---------------- NEXT EXAMS ----------------
#         next_exam = Exam.objects.filter(
#             user=user,
#             exam_id=exam.exam_id + 1
#         ).first()

#         next_next_exam = Exam.objects.filter(
#             user=user,
#             exam_id=exam.exam_id + 2
#         ).first()

#         next_exam_data = None
#         next_next_exam_data = None

#         # ---------------- NEXT EXAM ----------------
#         if next_exam:
#             next_exam.status = "up_next"

#             if score >= 50:
#                 next_exam.is_lock = True
#             else:
#                 next_exam.is_lock = False

#             next_exam.save()
#             next_exam_data = NextExamSerializer(next_exam).data

#         # ---------------- NEXT NEXT EXAM ----------------
#         if next_next_exam:
#             next_next_exam.status = "Locked"

#             if score >= 50:
#                 next_next_exam.is_lock = False
#             else:
#                 next_next_exam.is_lock = False

#             next_next_exam.save()
#             next_next_exam.refresh_from_db()
#             next_next_exam_data = NextExamSerializer(next_next_exam).data

#         # ---------------- RESPONSE ----------------
#         serializer = ExamCompleteSerializer(exam)

#         return Response({
#             "status": "success",
#             "status_code": status.HTTP_200_OK,
#             "message": "Exam processed successfully",
#             "data": {
#                 **serializer.data,
#                 "score": score,
#                 "mcq_submit": mcq_submit,

          
#                 "correct_answers": correct_answers,

#                 "is_lock": str(exam.is_lock),
#                 "completed_at": result.finished_date,
#                 "next_exam": next_exam_data,
#                 "next_next_exam": next_next_exam_data
#             }
#         })