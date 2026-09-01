from django.contrib import admin
from django.utils.html import format_html
import json
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    NCLEXCategory,
    NCLEXTopic,
    NCLEXSubtopic,
    NCLEXQuestion,
    QuestionOption,
    NCLEXExam,
    NCLEXExamResult,
    PracticeSession,
    Exam_question_result,
    PracticeQuestionResult,
)

# =========================================================
# Inlines
# =========================================================

class TopicInline(TabularInline):
    model = NCLEXTopic
    extra = 0


class SubtopicInline(TabularInline):
    model = NCLEXSubtopic
    extra = 0


class QuestionOptionInline(TabularInline):
    model = QuestionOption
    extra = 0
    ordering = ("order",)
    show_change_link = True
    fields = ("order", "text", "is_correct", "extra_data")


class ExamQuestionResultInline(TabularInline):
    model = Exam_question_result
    extra = 0
    show_change_link = True
    fields = (
        "question",
        "answer",
        "is_correct",
        "is_flagged",
        "is_skipped",
        "created_at",
    )
    readonly_fields = (
        "question",
        "answer",
        "is_correct",
        "is_flagged",
        "is_skipped",
        "created_at",
    )
    can_delete = False


# =========================================================
# Category & Taxonomy Admin
# =========================================================

@admin.register(NCLEXCategory)
class NCLEXCategoryAdmin(ModelAdmin):
    list_display = ("id", "title", "topics_count", "questions_count")
    search_fields = ("title",)
    ordering = ("title",)
    inlines = [TopicInline]

    def topics_count(self, obj):
        return obj.topics.count()
    topics_count.short_description = "Topics"

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Questions"


@admin.register(NCLEXTopic)
class NCLEXTopicAdmin(ModelAdmin):
    list_display = ("id", "title", "category", "subtopics_count", "questions_count")
    list_filter = ("category",)
    search_fields = ("title",)
    autocomplete_fields = ("category",)
    ordering = ("title",)
    inlines = [SubtopicInline]

    def subtopics_count(self, obj):
        return obj.subtopics.count()
    subtopics_count.short_description = "Subtopics"

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Questions"


@admin.register(NCLEXSubtopic)
class NCLEXSubtopicAdmin(ModelAdmin):
    list_display = ("id", "title", "topic", "category_name", "questions_count")
    list_filter = ("topic__category", "topic")
    search_fields = ("title", "description")
    autocomplete_fields = ("topic",)
    ordering = ("title",)

    def category_name(self, obj):
        return obj.topic.category.title if obj.topic and obj.topic.category else "-"
    category_name.short_description = "Client Needs Category"

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Questions"


# =========================================================
# NCLEX Questions Admin
# =========================================================

@admin.register(NCLEXQuestion)
class NCLEXQuestionAdmin(ModelAdmin):
    list_display = (
        "id",
        "question_preview",
        "type",
        "level",
        "category",
        "topic",
        "subtopic",
        "created_at",
    )
    list_filter = ("type", "level", "category", "topic")
    search_fields = ("question", "passage", "note")
    autocomplete_fields = ("category", "topic", "subtopic")
    inlines = [QuestionOptionInline]

    def question_preview(self, obj):
        return obj.question[:80] + "..." if len(obj.question) > 80 else obj.question
    question_preview.short_description = "Question Stem"


@admin.register(QuestionOption)
class NCLEXAnswerAdmin(ModelAdmin):
    list_display = ("id", "question", "text", "order", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text", "question__question")


# =========================================================
# NCLEX Final Exam Admin
# =========================================================

@admin.register(NCLEXExam)
class NCLEXExamAdmin(ModelAdmin):
    list_display = (
        "order",
        "title",
        "subtitle",
        "level",
        "tag",
        "total_question",
        "pool_questions_count",
        "time_limit_mins",
        "is_active",
    )
    list_editable = ("is_active",)
    filter_horizontal = ("questions",)
    search_fields = ("title", "subtitle", "tag")
    list_filter = ("level", "is_active")
    ordering = ("order",)

    fieldsets = (
        ("Exam Information", {
            "fields": ("order", "title", "subtitle", "tag", "level", "is_active"),
        }),
        ("Exam Delivery Configuration", {
            "fields": ("total_question", "time_limit_mins", "blueprint"),
            "description": "Defines how many questions are delivered (default 85) and the 150-minute time limit.",
        }),
        ("Question Pool", {
            "fields": ("questions",),
            "description": "Master pool of questions (approx. 200+ items). The Blueprint Engine randomly samples from this pool.",
        }),
    )

    def pool_questions_count(self, obj):
        count = obj.questions.count()
        return format_html("<b>{} questions</b>", count)
    pool_questions_count.short_description = "Questions in Pool"


# =========================================================
# Student Exam Attempt Results Admin
# =========================================================

@admin.register(NCLEXExamResult)
class NCLEXExamResultAdmin(ModelAdmin):
    list_display = (
        "id",
        "user_email",
        "exam_title",
        "status_badge",
        "score_badge",
        "readiness_badge",
        "total_correct",
        "total_incorrect",
        "total_skipped",
        "is_unlocked",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "is_unlocked", "exam")
    search_fields = ("user__email", "user__first_name", "user__last_name", "exam__title")
    ordering = ("-started_at",)
    inlines = [ExamQuestionResultInline]

    readonly_fields = (
        "user",
        "exam",
        "status",
        "score",
        "total_question",
        "total_correct",
        "total_incorrect",
        "total_skipped",
        "assigned_question_ids",
        "flagged_question_ids",
        "current_index",
        "analytics_preview",
        "started_at",
        "completed_at",
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Student"

    def exam_title(self, obj):
        return obj.exam.title
    exam_title.short_description = "Exam"

    def status_badge(self, obj):
        if obj.status == "completed":
            return format_html("<span style='color: green; font-weight: bold;'>✓ Completed</span>")
        return format_html("<span style='color: #d97706; font-weight: bold;'>⏳ In Progress</span>")
    status_badge.short_description = "Status"

    def score_badge(self, obj):
        if obj.status == "completed":
            color = "green" if obj.score >= 75.0 else ("#d97706" if obj.score >= 65.0 else "red")
            return format_html("<span style='color: {}; font-weight: bold;'>{:.1f}%</span>", color, obj.score)
        return "-"
    score_badge.short_description = "Score"

    def readiness_badge(self, obj):
        if obj.status == "completed" and isinstance(obj.analytics_data, dict):
            level = obj.analytics_data.get("readiness_level", "")
            if "Strong" in level:
                return format_html("<span style='background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Strong Readiness</span>")
            elif "Approaching" in level:
                return format_html("<span style='background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Approaching Readiness</span>")
            else:
                return format_html("<span style='background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 4px; font-weight: bold;'>Developing</span>")
        return "-"
    readiness_badge.short_description = "Readiness Level"

    def analytics_preview(self, obj):
        if obj.analytics_data:
            formatted_json = json.dumps(obj.analytics_data, indent=2)
            return format_html("<pre style='max-height: 400px; overflow: auto; background: #f8fafc; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px;'>{}</pre>", formatted_json)
        return "No analytics generated yet."
    analytics_preview.short_description = "Multi-Dimensional Diagnostic Analytics (JSON)"


# =========================================================
# Question Answer Results & Practice Admin
# =========================================================

@admin.register(Exam_question_result)
class ExamQuestionResultAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "exam",
        "question_preview",
        "is_correct",
        "is_flagged",
        "is_skipped",
        "created_at",
    )
    list_filter = ("is_correct", "is_flagged", "is_skipped", "exam")
    search_fields = ("user__email", "question__question")
    filter_horizontal = ("selected_answer",)

    def question_preview(self, obj):
        return obj.question.question[:60] if obj.question else "-"
    question_preview.short_description = "Question"


@admin.register(PracticeSession)
class PracticeSessionAdmin(ModelAdmin):
    list_display = ("user", "subtopic", "total_correct", "total_incorrect", "total_skipped", "created_at")
    filter_horizontal = ("question_set",)


@admin.register(PracticeQuestionResult)
class PracticeQuestionResultAdmin(ModelAdmin):
    list_display = ("session", "question", "answer", "is_correct", "created_at")