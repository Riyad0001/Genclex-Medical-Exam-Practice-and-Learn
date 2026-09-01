import email
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, ExpiredTokenError
from apps.user.models import User, UserProfile
from apps.user.services import send_welcome_email
from .serializers import RegisterSerializer, UserProfileSerializer
from apps.user import serializers
from rest_framework import generics
from apps.user.models import NursingProgram, StateCountry, AboutSource
from .serializers import NursingProgramSerializer, StateCountrySerializer, AboutSourceSerializer, AccountSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from .serializers import ForgotPasswordSerializer,  SetNewPasswordSerializer, GoogleLoginSerializer, ChangePasswordSerializer
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework.permissions import AllowAny
from apps.user.permission import IsNotBlacklisted
from apps.user.models import BlacklistedAccessToken
from apps.sub.models import Subscription, Plan
import requests 
from django.utils import timezone
import random
from django.utils import timezone
from datetime import timedelta
# from .models import EmailOTP
from apps.user.services import send_welcome_email
from django.core.mail import send_mail
from rest_framework import permissions
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
#-------------------------User Registeration Api View -------------------------#


def _build_auth_response(user, refresh, avatar=None):
    profile = UserProfile.objects.filter(user=user).first()
    is_profile_complete = False
    if profile:
        is_profile_complete = UserProfileSerializer(profile).data.get("is_profile_completed", False)

    payload = {
        "user": {
            "email": user.email,
        },
        "is_profile_complete": is_profile_complete,
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    }

    if avatar is not None:
        payload["user"].update(
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": avatar,
            }
        )

    return payload


def _flatten_serializer_errors(errors):
    flat_errors = {}
    for field, value in errors.items():
        if isinstance(value, list):
            flat_errors[field] = " ".join(str(item) for item in value)
        else:
            flat_errors[field] = str(value)
    return flat_errors


def _first_serializer_error_message(errors, default="Validation failed"):
    """Extract the first error message from serializer errors."""
    if not errors:
        return default
    
    # Get all error values into a single list
    all_messages = []
    
    for field, value in errors.items():
        if isinstance(value, list):
            for item in value:
                msg = str(item).strip()
                if msg:
                    all_messages.append(msg)
        else:
            msg = str(value).strip()
            if msg:
                all_messages.append(msg)
    
    # Return the first clean message
    if all_messages:
        return all_messages[0]
    
    return default

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_path = reverse("verify-email-redirect", kwargs={"uidb64": uid, "token": token})
            verify_link = request.build_absolute_uri(verify_path)

            email_sent = True
            email_error = None

            try:
                # Render HTML email template
                html_content = render_to_string('otp_email_template/email_verification.html', {
                    'user': user,
                    'verify_link': verify_link,
                    'company_name': getattr(settings, 'COMPANY_NAME', 'Our Platform'),
                })
                
                # Send HTML email
                email_message = EmailMessage(
                    subject='Verify Your Account',
                    body=html_content,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com'),
                    to=[user.email],
                )
                email_message.content_subtype = 'html'
                email_message.send(fail_silently=False)
            except Exception as e:
                email_sent = False
                email_error = str(e)

            return Response({
                "status": "success",
                "message": "Please verify your email",
                "email_sent": email_sent,
                "email_error": email_error,
                "data": {
                    "email": user.email,
                    "verify_link": verify_link
                }
            }, status=201)

        return Response({
            "status": "error",
            "message": _first_serializer_error_message(serializer.errors),
            "errors": _flatten_serializer_errors(serializer.errors)
        }, status=422)



class OTPVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")

        if not otp or not email:
            return Response({
                "status": "error",
                "message": "Email and OTP are required"
            }, status=422)

        user = User.objects.filter(email=email).first()

        if not user:
            return Response({
                "status": "error",
                "message": "Invalid email"
            }, status=422)

        if user.otp_verified:
            return Response({
                "status": "error",
                "message": "OTP already used"
            }, status=422)

        if user.otp != otp:
            return Response({
                "status": "error",
                "message": "Invalid OTP"
            }, status=422)

        if not user.otp_exp or user.otp_exp < timezone.now():
            return Response({
                "status": "error",
                "message": "OTP expired"
            }, status=422)

       
        user.otp_verified = True
        user.is_active = True 

        user.otp = None
        user.otp_exp = None

        user.save()

        return Response({
            "status": "success",
            "message": "Account verified successfully"
        }, status=200)


class VerifyEmailRedirectAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": "Invalid verification link"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired verification link"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        user.otp_verified = True
        user.is_active = True
        user.otp = None
        user.otp_exp = None
        user.save(update_fields=["otp_verified", "is_active", "otp", "otp_exp"])

        frontend_verify_url = getattr(settings, "FRONTEND_VERIFY_EMAIL_URL", "http://localhost:3000/login")
        return redirect(f"{frontend_verify_url}?verified=true")


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uidb64")
        token = request.data.get("token")

        if not uidb64 or not token:
            return Response(
                {"status": "error", "detail": "uidb64 and token are required"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"status": "error", "detail": "Invalid verification link"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"status": "error", "detail": "Invalid or expired verification link"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        user.otp_verified = True
        user.is_active = True
        user.otp = None
        user.otp_exp = None
        user.save(update_fields=["otp_verified", "is_active", "otp", "otp_exp"])

        return Response(
            {
                "status": "success",
                "message": "Account verified successfully",
                "data": {
                    "email": user.email,
                    "verified": True,
                },
            },
            status=status.HTTP_200_OK,
        )
    
#-------------------------User Login Api View -------------------------#

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response({
                "status": "error",
                "message": "Invalid email or password"
            }, status=401)

        
        if not user.otp_verified:
            return Response({
                "status": "error",
                "message": "Please verify OTP first"
            }, status=403)

        if not user.is_active:
            return Response({
                "status": "error",
                "message": "Account not activated"
            }, status=403)

        refresh = RefreshToken.for_user(user)
        profile = UserProfile.objects.filter(user=user).first()
        is_profile_complete = False
        if profile:
            is_profile_complete = UserProfileSerializer(profile).data.get("is_profile_completed", False)

        return Response({
            "user": {
                "email": user.email,
            },
            "is_profile_complete": is_profile_complete,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        }, status=200)
    

#-------------------------User Profile Api View -------------------------#

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated, IsNotBlacklisted]

    def _normalize_interval(self, interval):
        if not interval:
            return interval
        if interval == "month":
            return "monthly"
        if interval == "year":
            return "yearly"
        return interval

    def _build_subscription_data(self, user):
        sub = Subscription.objects.select_related("plan").filter(user=user).first()
        if not sub:
            return None

        is_trialing = (
            sub.trial_start is not None
            and sub.trial_end is not None
            and sub.trial_end > timezone.now()
        )

        normalized_interval = self._normalize_interval(sub.billing_interval)

        # 1) Use the direct FK relationship
        plan = sub.plan

        # 2) Fallback: match by package name + interval
        if not plan:
            plan = Plan.objects.filter(
                name=sub.package,
                interval=normalized_interval,
            ).first()

        # 3) Fallback: match by package name only
        if not plan:
            plan = Plan.objects.filter(name=sub.package).first()

        access_days = None
        if normalized_interval == "monthly":
            access_days = 30
        elif normalized_interval == "yearly":
            access_days = 365

        return {
            # "subscription_id": sub.id,
            "plan_id": plan.id if plan else None,
            "plan_name": plan.name if plan else None,
            # "package": sub.package,
            "billing_interval": sub.billing_interval,
            "is_active": sub.is_active,
            "auto_renew": sub.auto_renew,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "is_trialing": is_trialing,
            "trial_start": sub.trial_start,
            "trial_end": sub.trial_end,
            "package_price": float(plan.price) if plan else None,
            "access_days": access_days,
            "features": plan.features if plan else [],
        }

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)

        profile_photo_url = None
        if request.user.profile_photo:
            profile_photo_url = request.build_absolute_uri(
                request.user.profile_photo.url
            )

        return Response({
            "status": "success",
            "message": "Profile fetched successfully",
            "data": {
                **serializer.data,
                "full_name": f"{request.user.first_name} {request.user.last_name}".strip(),
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "profile_photo": profile_photo_url,
                "subscription": self._build_subscription_data(request.user),
            }
        }, status=200)

    def post(self, request):
        # Allow frontend to send selected ids for program/country/about_us
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Profile updated",
                "data": serializer.data
            }, status=200)

        # Flatten error messages to strings to prevent middleware issues
        error_msgs = {}
        for field, errs in serializer.errors.items():
            if isinstance(errs, list):
                error_msgs[field] = " ".join([str(e) for e in errs])
            else:
                error_msgs[field] = str(errs)

        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": error_msgs
        }, status=422)


class AccountAPIView(APIView):
    permission_classes = [IsAuthenticated, IsNotBlacklisted]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        serializer = AccountSerializer(request.user)
        return Response({
            "status": "success",
            "message": "Account fetched successfully",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = AccountSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Account updated successfully",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Validation failed",
            "errors": serializer.errors,
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def put(self, request):
        return self.patch(request)

    def delete(self, request):
        user = request.user
        if getattr(user, "profile_photo", None):
            user.profile_photo.delete(save=False)

        user.delete()
        return Response({
            "status": "success",
            "message": "Account deleted successfully",
        }, status=status.HTTP_200_OK)


# ------------------ Option List APIs ------------------#
class NursingProgramListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = NursingProgram.objects.all()
    serializer_class = NursingProgramSerializer


class StateCountryListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = StateCountry.objects.all()
    serializer_class = StateCountrySerializer


class AboutSourceListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = AboutSource.objects.all()
    serializer_class = AboutSourceSerializer

    
#--------------------------Forget Password Api View -------------------------#  

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_base_url = getattr(
            settings,
            "FRONTEND_RESET_PASSWORD_URL",
            "http://localhost:3000/auth/new-password",
        )
        reset_link = f"{reset_base_url}?uidb64={uid}&token={token}"

        try:
            # Render HTML email template
            html_content = render_to_string('otp_email_template/password_reset.html', {
                'user': user,
                'reset_link': reset_link,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Our Platform'),
            })
            
            # Send HTML email
            email_message = EmailMessage(
                subject='Reset Your Password',
                body=html_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com'),
                to=[user.email],
            )
            email_message.content_subtype = 'html'
            email_message.send(fail_silently=False)
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to send email: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Reset link sent to email",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class PasswordResetRedirectAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": "Invalid reset link"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired reset link"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        frontend_reset_url = getattr(settings, "FRONTEND_RESET_PASSWORD_URL", "http://localhost:3000/auth/new-password")
        return redirect(f"{frontend_reset_url}?uidb64={uidb64}&token={token}")


class SetNewPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uidb64")
        email = request.data.get("email")
        token = request.data.get("token")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not token:
            return Response({"detail": "Token is required"}, status=422)

        if password != confirm_password:
            return Response({"detail": "Passwords do not match"}, status=422)

        try:
            if uidb64:
                user_id = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=user_id)
            elif email:
                user = User.objects.get(email=email)
            else:
                return Response({"detail": "uidb64 or email is required"}, status=422)
        except Exception:
            return Response({"detail": "User not found"}, status=404)

        valid = default_token_generator.check_token(user, token)

        if not valid:
            return Response({"detail": "Invalid or expired token"}, status=422)

        user.set_password(password)
        user.save()

        return Response({"detail": "Password reset successful"}, status=200)



class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)

        serializer = GoogleLoginSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
      
        id_token = serializer.validated_data["id_token"]

        google_response = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token}
        ).json()

        if "email" not in google_response:
            return Response(
                {"detail": "Invalid Google token"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        if not google_response.get("email_verified"):
            return Response(
                {"detail": "Email not verified"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        email = google_response["email"].lower()
        first_name = google_response.get("given_name", "")
        last_name = google_response.get("family_name", "")
        avatar = google_response.get("picture")

        user = User.objects.filter(email=email).first()

        if not user:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_unusable_password()
            user.is_active = True
            user.otp_verified = True
            user.save(update_fields=["password", "is_active", "otp_verified"])
        else:
            changed_fields = []
            if first_name and not user.first_name:
                user.first_name = first_name
                changed_fields.append("first_name")
            if last_name and not user.last_name:
                user.last_name = last_name
                changed_fields.append("last_name")
            if not user.is_active:
                user.is_active = True
                changed_fields.append("is_active")
            if not user.otp_verified:
                user.otp_verified = True
                changed_fields.append("otp_verified")
            if changed_fields:
                user.save(update_fields=changed_fields)

        refresh = RefreshToken.for_user(user)
        return Response(_build_auth_response(user, refresh, avatar=avatar), status=200)
    
#----------------------------- Logout API View ---------------------------------#

class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes= []
    def post(self, request):
        refresh_token = request.data.get("refresh")
        access_token = request.headers.get("Authorization")

        if not refresh_token:
            return Response({
                "status": "error",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Refresh token is required"
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            # 🔹 Refresh token blacklist
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except ExpiredTokenError:
                # If the refresh token is expired, we can still blacklist it
                try:
                    token = RefreshToken(refresh_token, verify=False)
                    token.blacklist()
                except Exception:
                    pass
            except Exception:
                # If the refresh token is otherwise invalid/malformed, or database errors occur, do nothing
                pass

            # 🔹 Access token blacklist
            if access_token:
                try:
                    parts = access_token.split(" ")
                    if len(parts) > 1:
                        raw_access_token = parts[1]
                        try:
                            token_obj = AccessToken(raw_access_token)
                            jti = token_obj["jti"]
                            BlacklistedAccessToken.objects.get_or_create(jti=jti)
                        except ExpiredTokenError:
                            # If the access token is expired, we can decode with verify=False and blacklist it
                            try:
                                token_obj = AccessToken(raw_access_token, verify=False)
                                jti = token_obj["jti"]
                                BlacklistedAccessToken.objects.get_or_create(jti=jti)
                            except Exception:
                                pass
                        except Exception:
                            # If the access token is otherwise invalid/malformed, or database errors occur, do nothing
                            pass
                except Exception:
                    pass

            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Logout successful"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": f"Logout failed: {str(e)}"
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        


#----------------------------- Change Password API View ---------------------------------#

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated, IsNotBlacklisted]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({
                "status": "success",
                "message": "Password changed successfully."
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": _first_serializer_error_message(serializer.errors),
            "errors": _flatten_serializer_errors(serializer.errors)
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
