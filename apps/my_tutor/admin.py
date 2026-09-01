from django.contrib import admin

from .models import TutorChatMessage


@admin.register(TutorChatMessage)
class TutorChatMessageAdmin(admin.ModelAdmin):
	list_display = ("conversation_key", "role", "user", "created_at")
	list_filter = ("role", "created_at")
	search_fields = ("conversation_key", "content")
	ordering = ("-created_at",)
