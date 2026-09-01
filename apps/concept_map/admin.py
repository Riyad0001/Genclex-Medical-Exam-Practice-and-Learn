from django.contrib import admin

from .models import NursingConceptMap


@admin.register(NursingConceptMap)
class NursingConceptMapAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "updated_at")
    search_fields = ("user__username", "title")
    readonly_fields = ("created_at", "updated_at")
