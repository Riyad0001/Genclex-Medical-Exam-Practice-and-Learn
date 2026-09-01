from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Notification, NotificationPreference
from .services import send_notification


User = get_user_model()


class NotificationPreferenceAPITestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="tester@example.com",
			password="StrongPassword123",
		)
		self.user.otp_verified = True
		self.user.save(update_fields=["otp_verified"])
		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

	def test_get_notification_preferences_creates_defaults(self):
		response = self.client.get(reverse("notification-preferences"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["data"]["transaction_confirmation"])
		self.assertFalse(response.data["data"]["transaction_edited"])

		self.assertTrue(
			NotificationPreference.objects.filter(user=self.user).exists()
		)

	def test_patch_updates_notification_preferences(self):
		response = self.client.patch(
			reverse("notification-preferences"),
			{
				"transaction_confirmation": False,
				"payment_error": True,
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(response.data["data"]["transaction_confirmation"])
		self.assertTrue(response.data["data"]["payment_error"])

		preference = NotificationPreference.objects.get(user=self.user)
		self.assertFalse(preference.transaction_confirmation)
		self.assertTrue(preference.payment_error)

	def test_send_notification_returns_minimal_payload(self):
		response = send_notification(
			self.user,
			"transaction_confirmation",
			{"message": "Payment received successfully"},
		)

		self.assertEqual(response["message"], "Payment received successfully")
		self.assertIn("time", response)
		self.assertTrue(Notification.objects.filter(user=self.user, message="Payment received successfully").exists())

	def test_notifications_list_and_mark_read(self):
		notification = Notification.objects.create(
			user=self.user,
			event="subscription_created",
			message="Payment received successfully",
		)

		list_response = self.client.get(reverse("notifications-list"))
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(list_response.data["data"]["unread_count"], 1)
		self.assertEqual(list_response.data["data"]["notifications"][0]["message"], "Payment received successfully")
		self.assertFalse(list_response.data["data"]["notifications"][0]["is_read"])

		mark_read_response = self.client.patch(reverse("notifications-mark-read", args=[notification.pk]))
		self.assertEqual(mark_read_response.status_code, status.HTTP_200_OK)
		self.assertTrue(mark_read_response.data["data"]["is_read"])

		list_response2 = self.client.get(reverse("notifications-list"))
		self.assertEqual(list_response2.data["data"]["unread_count"], 0)

		notification.refresh_from_db()
		self.assertTrue(notification.is_read)
		self.assertIsNotNone(notification.read_at)
