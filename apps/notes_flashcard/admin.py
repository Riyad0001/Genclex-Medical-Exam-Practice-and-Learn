from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.notes_flashcard.models import FlashcardSet, NotesQuiz, NotesQuizProgress

@admin.register(FlashcardSet)
class FlashcardSetAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "program",
        "cards_requested",
        "file_name",
        "created_at",
    )

    list_filter = (
        "created_at",
        "program",
    )

    search_fields = (
        "user__email",
        "user__username",
        "program",
        "file_name",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Flashcard Information",
            {
                "fields": (
                    "user",
                    "program",
                    "cards_requested",
                    "file_name",
                    "created_at",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "content_source",
                    "flashcards",
                ),
                "classes": ("tab",),
            },
        ),
    )


@admin.register(NotesQuiz)
class NotesQuizAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "program",
        "question_format",
        "question_requested",
        "content_file",
        "created_at",
    )

    list_filter = (
        "created_at",
        "program",
        "question_format",
    )

    search_fields = (
        "user__email",
        "user__username",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Quiz Information",
            {
                "fields": (
                    "user",
                    "program",
                    "question_format",
                    "question_requested",
                    "content_file",
                    "created_at",
                )
            },
        ),
        (
            "Quiz Content",
            {
                "fields": (
                    "content_source",
                    "nclex_quiz",
                ),
                "classes": ("tab",),
            },
        ),
    )


@admin.register(NotesQuizProgress)
class NotesQuizProgressAdmin(ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "question_index",
        "user_answer",
        "is_correct",
        "updated_at",
    )
    list_filter = ("is_correct", "updated_at")
    ordering = ("quiz", "question_index")



