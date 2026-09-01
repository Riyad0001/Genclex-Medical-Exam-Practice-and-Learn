from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "transaction_confirmation",
            "transaction_edited",
            "transaction_invoice",
            "transaction_cancelled",
            "transaction_refund",
            "payment_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "event",
            "message",
            "is_read",
            "created_at",
            "read_at",
        ]
        read_only_fields = ["id", "event", "message", "created_at", "read_at"]