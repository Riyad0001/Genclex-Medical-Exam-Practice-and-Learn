from django.urls import path
from .views import CategoryContentAPIView, AnswerSubmitAPIView, FlashcardProgressAPIView

urlpatterns = [
    path("category-content/", CategoryContentAPIView.as_view(), name="category-content"),
    path("answer-submit/", AnswerSubmitAPIView.as_view(), name="answer-submit"),
    path("falscard-progress/", FlashcardProgressAPIView.as_view(), name="answer-submit"),
   
   
] 

