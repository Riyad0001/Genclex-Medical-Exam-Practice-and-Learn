from django.urls import path
from .views import (
    ForgotPasswordAPIView, LoginAPIView, OTPVerifyAPIView,
    RegisterAPIView, UserProfileView, SetNewPasswordAPIView,
    GoogleLoginAPIView, LogoutView,
    NursingProgramListAPIView, StateCountryListAPIView, AboutSourceListAPIView,
    PasswordResetRedirectAPIView, VerifyEmailRedirectAPIView, VerifyEmailAPIView,
    AccountAPIView, ChangePasswordAPIView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', OTPVerifyAPIView.as_view(), name='verify-otp'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailRedirectAPIView.as_view(), name='verify-email-redirect'),
    path('verify-email-json/', VerifyEmailAPIView.as_view(), name='verify-email-json'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('account/', AccountAPIView.as_view(), name='account'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forget-password'),
    path('reset-password/<uidb64>/<token>/', PasswordResetRedirectAPIView.as_view(), name='reset-password-redirect'),
    path('set-new-password/', SetNewPasswordAPIView.as_view(), name='set-new-password' ),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
    path("google-login/", GoogleLoginAPIView.as_view(), name='google-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # Dynamic option lists for the signup/profile form
    path('options/programs/', NursingProgramListAPIView.as_view(), name='program-list'),
    path('options/states/', StateCountryListAPIView.as_view(), name='state-list'),
    path('options/sources/', AboutSourceListAPIView.as_view(), name='source-list'),
]


