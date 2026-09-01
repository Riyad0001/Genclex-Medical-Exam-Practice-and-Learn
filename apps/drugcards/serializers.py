from rest_framework import serializers

from .models import DrugCardHistory


class DrugCardHistorySerializer(serializers.ModelSerializer):
    """Full serializer — used when returning a single history record (includes card_data)."""

    class Meta:
        model = DrugCardHistory
        fields = ["id", "drug_name", "card_data", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DrugCardHistoryListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer — omits the full card_data JSON."""

    class Meta:
        model = DrugCardHistory
        fields = ["id", "drug_name", "created_at", "updated_at"]
        read_only_fields = fields
