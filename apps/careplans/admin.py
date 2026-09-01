from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import CarePlanHistory


@admin.register(CarePlanHistory)
class CarePlanHistoryAdmin(ModelAdmin):
    list_display = ["id", "user", "title", "created_at", "updated_at"]
    list_filter = ["user", "created_at"]
    search_fields = ["user__email", "title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
