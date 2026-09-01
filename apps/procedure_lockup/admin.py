
from django.contrib import admin
from apps.procedure_lockup.models import ProcedureModule, Lecture_Notes
from unfold.admin import ModelAdmin

@admin.register(ProcedureModule)
class ProcedureModuleAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    ordering = ("id",)
    inlines = []



@admin.register(Lecture_Notes)
class LectureNotesAdmin(ModelAdmin):
    list_display = (
        "title",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "user_html",
        "formatted_html",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("id",)
    inlines = []

