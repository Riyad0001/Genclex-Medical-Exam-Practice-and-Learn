from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class LoginAPIViewTestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="login@example.com",
			password="StrongPassword123",
		)
		self.user.otp_verified = True
		self.user.is_active = True
		self.user.save(update_fields=["otp_verified", "is_active"])

	def test_login_returns_is_profile_complete_false_when_profile_missing(self):
		response = self.client.post(
			reverse("login"),
			{
				"email": "login@example.com",
				"password": "StrongPassword123",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("is_profile_complete", response.data["data"])
		self.assertFalse(response.data["data"]["is_profile_complete"])


class GoogleLoginAPIViewTestCase(APITestCase):
	@patch("apps.user.views.requests.get")
	def test_google_login_returns_same_auth_shape(self, mock_requests_get):
		mock_requests_get.return_value.json.return_value = {
			"email": "google@example.com",
			"email_verified": True,
			"given_name": "Google",
			"family_name": "User",
			"picture": "https://example.com/avatar.png",
		}

		response = self.client.post(
			reverse("google-login"),
			{"id_token": "fake-token"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("is_profile_complete", response.data["data"])
		self.assertFalse(response.data["data"]["is_profile_complete"])
		self.assertEqual(response.data["data"]["user"]["email"], "google@example.com")
		self.assertIn("tokens", response.data["data"])


class RegisterAPIViewTestCase(APITestCase):
	def test_register_duplicate_email_returns_422_with_error(self):
		User.objects.create_user(
			email="register@example.com",
			password="StrongPassword123",
		)

		response = self.client.post(
			reverse("register"),
			{
				"first_name": "Test",
				"last_name": "User",
				"email": "register@example.com",
				"password": "StrongPassword123",
				"confirm_password": "StrongPassword123",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertFalse(response.data["success"])
		self.assertIn("Email already exists", response.data["message"])


class ChangePasswordAPIViewTestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="change@example.com",
			password="OldPassword123",
		)
		self.user.otp_verified = True
		self.user.is_active = True
		self.user.save(update_fields=["otp_verified", "is_active"])
		
		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

	def test_change_password_success(self):
		response = self.client.post(
			reverse("change-password"),
			{
				"current_password": "OldPassword123",
				"new_password": "NewPassword123",
				"confirm_new_password": "NewPassword123",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["message"], "Password changed successfully.")
		
		# Verify authentication with the new password
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password("NewPassword123"))

	def test_change_password_incorrect_current_password(self):
		response = self.client.post(
			reverse("change-password"),
			{
				"current_password": "WrongPassword123",
				"new_password": "NewPassword123",
				"confirm_new_password": "NewPassword123",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertFalse(response.data["success"])
		self.assertIn("Current password", response.data["message"])

	def test_change_password_mismatched_new_passwords(self):
		response = self.client.post(
			reverse("change-password"),
			{
				"current_password": "OldPassword123",
				"new_password": "NewPassword123",
				"confirm_new_password": "MismatchedPassword123",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertFalse(response.data["success"])
		self.assertIn("match", response.data["message"])

	def test_change_password_too_short(self):
		response = self.client.post(
			reverse("change-password"),
			{
				"current_password": "OldPassword123",
				"new_password": "short",
				"confirm_new_password": "short",
			},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertFalse(response.data["success"])
		self.assertIn("at least 8 characters", response.data["message"])


class LogoutViewTestCase(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="logout@example.com",
			password="StrongPassword123",
		)
		self.user.otp_verified = True
		self.user.is_active = True
		self.user.save(update_fields=["otp_verified", "is_active"])

	def test_logout_success_with_valid_tokens(self):
		refresh = RefreshToken.for_user(self.user)
		access_token = str(refresh.access_token)
		refresh_token = str(refresh)

		response = self.client.post(
			reverse("logout"),
			{"refresh": refresh_token},
			HTTP_AUTHORIZATION=f"Bearer {access_token}",
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["message"], "Logout successful")

	def test_logout_success_with_expired_tokens(self):
		from datetime import timedelta
		from apps.user.models import BlacklistedAccessToken

		refresh = RefreshToken.for_user(self.user)
		# Force refresh token expiration
		refresh.set_exp(lifetime=-timedelta(days=1))
		refresh_token_str = str(refresh)

		# Force access token expiration
		access = refresh.access_token
		access.set_exp(lifetime=-timedelta(days=1))
		access_token_str = str(access)
		
		# Get access token JTI to verify blacklisting
		jti = access["jti"]

		response = self.client.post(
			reverse("logout"),
			{"refresh": refresh_token_str},
			HTTP_AUTHORIZATION=f"Bearer {access_token_str}",
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["message"], "Logout successful")

		# Verify access token is blacklisted
		self.assertTrue(BlacklistedAccessToken.objects.filter(jti=jti).exists())

	def test_logout_success_with_invalid_malformed_tokens(self):
		from apps.user.models import BlacklistedAccessToken
		
		initial_count = BlacklistedAccessToken.objects.count()

		response = self.client.post(
			reverse("logout"),
			{"refresh": "completely-invalid-refresh-token"},
			HTTP_AUTHORIZATION="Bearer completely-invalid-access-token",
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["message"], "Logout successful")
		
		# No new blacklist records should be created since tokens are completely invalid
		self.assertEqual(BlacklistedAccessToken.objects.count(), initial_count)

	def test_logout_success_with_uuid_user_id(self):
		refresh = RefreshToken.for_user(self.user)
		# Mock the user_id claim to be a UUID string
		refresh.payload["user_id"] = "212eb9aa-083d-4d6d-a6c8-853d6a1f38f9"
		refresh_token_str = str(refresh)

		response = self.client.post(
			reverse("logout"),
			{"refresh": refresh_token_str},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data["success"])
		self.assertEqual(response.data["message"], "Logout successful")

	def test_logout_fails_with_missing_refresh_token(self):
		response = self.client.post(
			reverse("logout"),
			{},
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
		self.assertFalse(response.data["success"])
		self.assertIn("Refresh token is required", response.data["message"])
