from django.urls import path
from .views import (
    NCLEXPracticeAPIView,
    NCLEXPracticeSessionAPIView,
    NCLEXPracticeExamAPIVieiw,
    NCLEXPracticeAnswerAPIView,
    NCLEXPracticeFinishAPIView,
    NCLEXExamListAPIView,
    NCLEXExamStartAPIView,
    NCLEXExamQuestionsAPIView,
    NCLEXExamAnswerAPIView,
    NCLEXExamFlagAPIView,
    NCLEXExamSummaryAPIView,
    NCLEXExamFinishAPIView,
    NCLEXExamReviewAPIView,
)

urlpatterns = [
    # =========================================================================
    # NCLEX PRACTICE APIS (Topic / Subtopic Practice)
    # =========================================================================
    path("nclex/practice/", NCLEXPracticeAPIView.as_view(), name="nclex-practice-list"),
    path("nclex/practice/session/", NCLEXPracticeSessionAPIView.as_view(), name="nclex-practice-session-list"),
    path("nclex/practice/exam/<int:session_id>/", NCLEXPracticeExamAPIVieiw.as_view(), name="nclex-practice-exam-question"),
    path("nclex/practice/answer/", NCLEXPracticeAnswerAPIView.as_view(), name="nclex-practice-answer"),
    path("nclex/practice/finish/<int:session_id>/", NCLEXPracticeFinishAPIView.as_view(), name="nclex-practice-finish"),

    # =========================================================================
    # NCLEX FINAL EXAM APIS (5-Stage Exam Simulator with Progressive Unlocking)
    # =========================================================================
    path("nclex/exams/", NCLEXExamListAPIView.as_view(), name="nclex-exam-list"),
    path("nclex/exams/<int:exam_id>/start/", NCLEXExamStartAPIView.as_view(), name="nclex-exam-start"),
    path("nclex/exams/session/<int:session_id>/questions/", NCLEXExamQuestionsAPIView.as_view(), name="nclex-exam-session-questions"),
    path("nclex/exams/answer/", NCLEXExamAnswerAPIView.as_view(), name="nclex-exam-answer-submit"),
    path("nclex/exams/session/<int:session_id>/flag/", NCLEXExamFlagAPIView.as_view(), name="nclex-exam-flag"),
    path("nclex/exams/session/<int:session_id>/summary/", NCLEXExamSummaryAPIView.as_view(), name="nclex-exam-summary"),
    path("nclex/exams/finish/<int:session_id>/", NCLEXExamFinishAPIView.as_view(), name="nclex-exam-finish"),
    path("nclex/exams/review/<int:session_id>/", NCLEXExamReviewAPIView.as_view(), name="nclex-exam-review"),
]


