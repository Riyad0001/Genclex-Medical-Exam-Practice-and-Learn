from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
	list_display = (
		"user",
		"transaction_confirmation",
		"transaction_edited",
		"transaction_invoice",
		"transaction_cancelled",
		"transaction_refund",
		"payment_error",
		"updated_at",
	)
	search_fields = ("user__email",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = (
		"user",
		"event",
		"message",
		"is_read",
		"created_at",
	)
	list_filter = ("is_read", "created_at")
	search_fields = ("user__email", "message", "event")
