from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notification_preference",
	)
	transaction_confirmation = models.BooleanField(default=True)
	transaction_edited = models.BooleanField(default=False)
	transaction_invoice = models.BooleanField(default=True)
	transaction_cancelled = models.BooleanField(default=True)
	transaction_refund = models.BooleanField(default=True)
	payment_error = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-updated_at"]

	def __str__(self):
		return f"Notification preferences for {self.user}"


class Notification(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notifications",
	)
	event = models.CharField(max_length=100, blank=True)
	message = models.TextField()
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	read_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ["-created_at"]

	def mark_read(self):
		if not self.is_read:
			from django.utils import timezone

			self.is_read = True
			self.read_at = timezone.now()
			self.save(update_fields=["is_read", "read_at"])

	def __str__(self):
		return f"Notification for {self.user}: {self.message}"
