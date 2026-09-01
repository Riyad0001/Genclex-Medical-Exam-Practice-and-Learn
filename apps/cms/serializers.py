from rest_framework import serializers
from .models import (
    LandingHero,
    LandingStatsBanner,
    AITutorSpotlight,
    LandingFeature,
    PillarsSection,
    AIToolCard,
)


class LandingHeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingHero
        fields = [
            "id",
            "badge_text",
            "title",
            "title_highlight",
            "description",
            "badge_tags",
            "primary_cta_text",
            "primary_cta_link",
            "secondary_cta_text",
            "secondary_cta_link",
            "trust_text",
            "hero_image",
            "floating_features",
            "is_active",
            "created_at",
            "updated_at",
        ]


class LandingStatsBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingStatsBanner
        fields = [
            "id",
            "title",
            "pills",
            "stats",
            "is_active",
            "created_at",
            "updated_at",
        ]


class AITutorSpotlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITutorSpotlight
        fields = [
            "id",
            "tag",
            "heading",
            "description",
            "languages",
            "features",
            "preview_image",
            "is_active",
            "created_at",
            "updated_at",
        ]


class LandingFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingFeature
        fields = [
            "id",
            "step_number",
            "title",
            "subtitle",
            "description",
            "bullets",
            "image",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]


class PillarsSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PillarsSection
        fields = [
            "id",
            "tag",
            "heading",
            "description",
            "highlight_badge",
            "pillars",
            "is_active",
            "created_at",
            "updated_at",
        ]


class AIToolCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIToolCard
        fields = [
            "id",
            "title",
            "description",
            "icon",
            "image",
            "badge",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]


class LandingPageSerializer(serializers.Serializer):
    hero = LandingHeroSerializer(read_only=True, allow_null=True)
    stats_banner = LandingStatsBannerSerializer(read_only=True, allow_null=True)
    ai_tutor_spotlight = AITutorSpotlightSerializer(read_only=True, allow_null=True)
    features_header = serializers.DictField(read_only=True)
    features = LandingFeatureSerializer(many=True, read_only=True)
    pillars = PillarsSectionSerializer(read_only=True, allow_null=True)
    ai_tools_header = serializers.DictField(read_only=True)
    ai_tools = AIToolCardSerializer(many=True, read_only=True)
