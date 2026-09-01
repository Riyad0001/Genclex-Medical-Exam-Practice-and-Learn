from django.contrib import admin

from .models import DrugCardHistory


@admin.register(DrugCardHistory)
class DrugCardHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "drug_name", "created_at")
    list_filter = ("created_at",)
    search_fields = ("drug_name", "user__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
