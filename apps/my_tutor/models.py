from django.conf import settings
from django.db import models


class TutorChatMessage(models.Model):
	ROLE_USER = "user"
	ROLE_ASSISTANT = "assistant"

	ROLE_CHOICES = (
		(ROLE_USER, "User"),
		(ROLE_ASSISTANT, "Assistant"),
	)

	conversation_key = models.CharField(max_length=255, db_index=True)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="tutor_chat_messages",
	)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)
	content = models.JSONField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at", "id"]
		indexes = [models.Index(fields=["conversation_key", "created_at"])]

	def __str__(self):
		return f"{self.conversation_key} - {self.role} - {self.created_at:%Y-%m-%d %H:%M:%S}"
