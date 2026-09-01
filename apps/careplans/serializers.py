from rest_framework import serializers

from .models import CarePlanHistory


class GenerateRequestSerializer(serializers.Serializer):
    """Mirrors backend_api.py's GenerateRequest(BaseModel): patient: dict[str, Any]"""
    patient = serializers.DictField()


class EditRequestSerializer(serializers.Serializer):
    """Mirrors backend_api.py's EditRequest(BaseModel):
    instruction: str = Field(min_length=1)
    care_plan: dict[str, Any]
    """
    instruction = serializers.CharField(min_length=1)
    care_plan = serializers.DictField()


class CarePlanHistorySerializer(serializers.ModelSerializer):
    """Full serializer — used when returning a single history record."""
    subtitle = serializers.CharField(read_only=True)

    class Meta:
        model = CarePlanHistory
        fields = ["id", "title", "subtitle", "care_plan", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CarePlanHistoryListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer — omits the full care_plan JSON."""
    subtitle = serializers.CharField(read_only=True)

    class Meta:
        model = CarePlanHistory
        fields = ["id", "title", "subtitle", "created_at", "updated_at"]
        read_only_fields = fields
