from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline

from .models import (
    LearningCategory,
    LearningContent,
    SavedNotes,
    LearningProgress,
    Library,
    LearningProgress,
    LearningContentIcon,
    LearningContentColor,
)

@admin.register(LearningCategory)
class LearningCategoryAdmin(ModelAdmin):
    list_display = ("topic", "title", "subtitle", "created_at")
    search_fields = ("topic", "title")
    list_filter = ("topic", "created_at")
    ordering = ("id",)
    inlines = []


@admin.register(LearningContent)
class LearningContentAdmin(ModelAdmin):
    list_display = ("category", "content_name", "is_active", "created_at")
    search_fields = ("content_name",)
    list_filter = ("category__topic", "category", "is_active", "created_at")
    ordering = ("id",)
    list_filter_sheet = False



@admin.register(SavedNotes)
class SavedNotesAdmin(ModelAdmin):
    list_display = ("user", "content", "created_at")
    search_fields = ("user__username", "content__content_name")
    list_filter = ("created_at",)
    ordering = ("created_at",)

@admin.register(LearningProgress)
class LearningProgressAdmin(ModelAdmin):
    list_display = ("user", "content", "is_completed", "completed_at")
    search_fields = ("user__username", "content__content_name")
    list_filter = ("is_completed", "completed_at")
    ordering = ("completed_at",)

@admin.register(Library)
class LibraryAdmin(ModelAdmin):
    list_display = ("user", "name", "icon_preview", "is_active", "created_at")
    search_fields = ("user__username", "name")
    list_filter = ("is_active", "created_at")
    ordering = ("created_at",)

    @admin.display(description="Icon")
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 4px;" />',
                obj.icon.icon.url,
            )
        return "-"


@admin.register
class LearningProgressAdmin(ModelAdmin):
    list_display = ('user', 'content', 'is_completed', 'completed_at')


@admin.register(LearningContentIcon)
class LearningIconAdmin(ModelAdmin):
    list_display = ["icon", "id", "is_active", "created_at"]

@admin.register(LearningContentColor)
class LearningColorAdmin(ModelAdmin):
    list_display = ["color", "id", "is_active", "created_at"]