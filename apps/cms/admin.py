from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    LandingHero,
    LandingStatsBanner,
    AITutorSpotlight,
    LandingFeature,
    PillarsSection,
    AIToolCard,
)


@admin.register(LandingHero)
class LandingHeroAdmin(ModelAdmin):
    list_display = ("title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "badge_text", "description")


@admin.register(LandingStatsBanner)
class LandingStatsBannerAdmin(ModelAdmin):
    list_display = ("title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)


@admin.register(AITutorSpotlight)
class AITutorSpotlightAdmin(ModelAdmin):
    list_display = ("heading", "tag", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("heading", "description")


@admin.register(LandingFeature)
class LandingFeatureAdmin(ModelAdmin):
    list_display = ("step_number", "title", "subtitle", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "description")
    ordering = ("order", "step_number")


@admin.register(PillarsSection)
class PillarsSectionAdmin(ModelAdmin):
    list_display = ("heading", "tag", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("heading", "description")


@admin.register(AIToolCard)
class AIToolCardAdmin(ModelAdmin):
    list_display = ("title", "badge", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("order",)
