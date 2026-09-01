
from django.urls import path
from .views import *

urlpatterns = [
    
    path("flashcards/generate/", generate_flashcards),
    path("flashcards_list/", get_list),
    path("flashcards/<int:pk>/", get_flashcard),

    # Flashcard progress / session
    path("flashcards/<int:pk>/mark/", mark_flashcard),
    path("flashcards/<int:pk>/score/", session_score),
    path("flashcards/<int:pk>/still-learning/", practice_still_learning),
    path("flashcards/<int:pk>/restart/", restart_all),

    # Flashcard history delete
    path("flashcards/<int:pk>/delete/", delete_flashcard_set),
    path("flashcards/clear/", delete_all_flashcard_sets),


    # --------------------------- nclex_quiz ---------------------------- #
    path("nclex/generate/", generate_nclex_quiz),
    path("nclex/<int:pk>/", get_nclex_quiz),
    path("nclex/", list_nclex_quiz),

    # NCLEX quiz exam taking & progress score
    path("nclex/<int:pk>/submit/", submit_nclex_answer),
    path("nclex/<int:pk>/score/", get_nclex_quiz_score),
    path("nclex/<int:pk>/restart/", restart_nclex_quiz),

    # NCLEX quiz delete
    path("nclex/<int:pk>/delete/", delete_nclex_quiz),
    path("nclex/clear/", delete_all_nclex_quizzes),
    
]

