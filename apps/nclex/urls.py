
from django.urls import path
from .views import CalculatorAPIView, ExamQuestionView, SubmitExamView, CompleteExamView, ExamDetailView,ExamQuestionView

urlpatterns = [
    path('calculator/', CalculatorAPIView.as_view(), name='calculator'), # Calculator
    path('exam/<int:exam_id>/questions/', ExamQuestionView.as_view(),name='exam-questions'),  # Exam Questions
    path('submit-answer/', SubmitExamView.as_view(), name='submit-answer'),  # Submit answer
    path('complete-exam/', CompleteExamView.as_view(), name='complete-exam'),  # Completed Exam
    path("exam/<int:exam_id>/", ExamDetailView.as_view(), name="exam-detail-view"),  # Exam Details (Review Result)
    path("exam/<int:exam_id>/review/", ExamQuestionView.as_view(), name="exam-question-view"),
]


