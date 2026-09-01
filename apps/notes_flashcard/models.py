from django.db import models

from project import settings



class FlashcardSet(models.Model):
    PROGRAM_CHOICES = [
        ("LPN", "LPN/LVN"),
        ("RN", "RN"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcard_sets"
    )
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, default="RN")
    cards_requested = models.IntegerField(default=30)
    flashcards = models.JSONField()
    file_name = models.CharField(max_length=255, blank=True, null=True)
    content_source = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_program_display()} — {self.file_name or 'Manual'}"


class FlashcardProgress(models.Model):
    """
    Tracks per-card learning status within a FlashcardSet.

    card_index maps to the position in FlashcardSet.flashcards[] (0-based).
    know_it = True  -> user marked "Know It"
    know_it = False -> user marked "Still Learning"
    know_it = None  -> not yet reviewed (default)
    """

    flashcard_set = models.ForeignKey(
        FlashcardSet,
        on_delete=models.CASCADE,
        related_name="progress",
    )
    card_index = models.IntegerField()
    know_it = models.BooleanField(null=True, default=None)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("flashcard_set", "card_index")
        ordering = ["card_index"]

    def __str__(self):
        status = "Know It" if self.know_it else ("Still Learning" if self.know_it is False else "Not Reviewed")
        return f"Set {self.flashcard_set_id} / Card {self.card_index} — {status}"


class NotesQuiz(models.Model):
    PROGRAM_CHOICES = [
        ("LPN", "LPN/LVN"),
        ("RN", "RN"),
    ]
    QUESTION_FORMAT_CHOICES = [
        ("MCQ", "Standard Multiple Choice (MCQ)"),
        ("SATA", "Select All That Apply (SATA)"),
        ("NGN", "Next-Generation (NGN) Case Studies"),
        ("FITB", "Fill-in-the-Blank"),
        ("MIX", "Mix and Match All Types"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes_quiz"
    )
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, default="RN")
    question_format = models.CharField(
        max_length=10,
        choices=QUESTION_FORMAT_CHOICES,
        default="MCQ",
    )
    question_requested = models.IntegerField(default=30)
    nclex_quiz = models.JSONField()
    content_file = models.FileField(upload_to="notes/", blank=True, null=True)
    content_source = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_program_display()} — {self.get_question_format_display()}"


class NotesQuizProgress(models.Model):
    """
    Tracks user answers and correctness for questions in a NotesQuiz set.

    question_index maps to the 0-based position in NotesQuiz.nclex_quiz[].
    user_answer stores the user's submitted answer ("A", ["A", "C"], or "60-100").
    is_correct boolean indicating if the answer was correct.
    """

    quiz = models.ForeignKey(
        NotesQuiz,
        on_delete=models.CASCADE,
        related_name="progress",
    )
    question_index = models.IntegerField()
    user_answer = models.JSONField()
    is_correct = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("quiz", "question_index")
        ordering = ["question_index"]

    def __str__(self):
        status_str = "Correct" if self.is_correct else "Incorrect"
        return f"Quiz {self.quiz_id} / Question {self.question_index} — {status_str}"

