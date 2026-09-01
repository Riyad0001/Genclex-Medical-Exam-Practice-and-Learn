import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)


from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        if User.objects.filter(email=email).exists():
            raise ValueError("Email already exists")

        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields["is_staff"]:
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with soft delete support."""
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_exp = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)       
    
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token_exp = models.DateTimeField(null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)

    # password = models.CharField(max_length=128, blank = True, null=True)  # Inherited from AbstractBaseUser

    objects = UserManager()
    # all_objects = BaseUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email


#--------------------- Access Token Blacklist -----------------#
class BlacklistedAccessToken(models.Model):
    jti = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


#------------------- USER PROFILE --------------------#

class UserProfile(models.Model):
    # These fields were previously choice-based strings. They are now
    # ForeignKeys to dynamic tables so front-end can fetch id/name lists
    # and pass the selected id when saving/updating the profile.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    program = models.ForeignKey(
        'NursingProgram', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles'
    )
    country = models.ForeignKey(
        'StateCountry', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles'
    )
    about_us = models.ForeignKey(
        'AboutSource', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles'
    )
    university = models.CharField(max_length=100, blank=True)
    # Whether user accepted terms and privacy via frontend during signup/profile
    terms_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} Profile"


# ------------------ Dynamic option tables -----------------#
class NursingProgram(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class StateCountry(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'State/Country'
        verbose_name_plural = 'States/Countries'
        ordering = ['name']

    def __str__(self):
        return self.name


class AboutSource(models.Model):
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    