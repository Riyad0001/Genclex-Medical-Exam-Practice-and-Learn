from django.urls import path
from .views import AIFormatAPIView, ProcedureAPI, NoteAPIView

urlpatterns = [
    
    path('procedure/', ProcedureAPI.as_view()),         
    path('procedure/<int:pk>/', ProcedureAPI.as_view()),


    # ---------------------------Lecture_Notes ---------------------------- #
    path("ai-format/", AIFormatAPIView.as_view()),

    path("notes/", NoteAPIView.as_view(), name="note-list-create"),
    path("notes/<int:pk>/", NoteAPIView.as_view(), name="note-detail"),
   
]

