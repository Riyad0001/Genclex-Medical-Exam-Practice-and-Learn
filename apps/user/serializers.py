from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import UserProfile
User = get_user_model()

from .models import NursingProgram, StateCountry, AboutSource


#----------------------------- User Serializer ------------------------#
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[])
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")

        if len(attrs['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )

        user.is_active = False
        user.save()

        return user


class AccountSerializer(serializers.ModelSerializer):
    remove_profile_photo = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'profile_photo',
            'remove_profile_photo',
        ]
        extra_kwargs = {
            'profile_photo': {'required': False, 'allow_null': True},
            'email': {'read_only': True},
        }


    def update(self, instance, validated_data):
        remove_profile_photo = validated_data.pop('remove_profile_photo', False)
        profile_photo = validated_data.pop('profile_photo', serializers.empty)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if remove_profile_photo:
            if instance.profile_photo:
                instance.profile_photo.delete(save=False)
            instance.profile_photo = None
        elif profile_photo is not serializers.empty:
            if instance.profile_photo and instance.profile_photo != profile_photo:
                instance.profile_photo.delete(save=False)
            instance.profile_photo = profile_photo

        instance.save()
        return instance


#----------------------------- User Profile Serializer ------------------------#

class UserProfileSerializer(serializers.ModelSerializer):
    # frontend will pass ids for program/country/about_us
    program = serializers.PrimaryKeyRelatedField(
        queryset=NursingProgram.objects.all(), allow_null=True, required=False
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=StateCountry.objects.all(), allow_null=True, required=False
    )
    about_us = serializers.PrimaryKeyRelatedField(
        queryset=AboutSource.objects.all(), allow_null=True, required=False
    )

    program_display = serializers.SerializerMethodField()
    country_display = serializers.SerializerMethodField()
    about_us_display = serializers.SerializerMethodField()

    is_profile_completed = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = [
            "program", "program_display",
            "university",
            "country", "country_display",
            "about_us", "about_us_display",
            "terms_accepted", "privacy_accepted",
            "is_profile_completed"
        ]

    def _safe_related(self, obj, attr_name):
        try:
            return getattr(obj, attr_name)
        except Exception:
            return None

    def get_is_profile_completed(self, obj):
        # check required fields filled or not
        required_fields = [
            self._safe_related(obj, "program") is not None,
            bool(obj.university),
            self._safe_related(obj, "country") is not None,
            self._safe_related(obj, "about_us") is not None,
            # obj.terms_accepted,
            # obj.privacy_accepted,
        ]

        return all(required_fields)

    def get_program_display(self, obj):
        program = self._safe_related(obj, "program")
        return getattr(program, "name", None)

    def get_country_display(self, obj):
        country = self._safe_related(obj, "country")
        return getattr(country, "name", None)

    def get_about_us_display(self, obj):
        about_us = self._safe_related(obj, "about_us")
        return getattr(about_us, "name", None)


# Simple serializers for the option tables
class NursingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingProgram
        fields = ['id', 'name']


class StateCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StateCountry
        fields = ['id', 'name']


class AboutSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutSource
        fields = ['id', 'name']

#----------------------------- Forgot Password Serializer ------------------------#

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


#----------------------------- New Password Serializer----------------------------#

class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    

#---------------------------- Google Login Serializer----------------------------#

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


#---------------------------- Change Password Serializer-------------------------#

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        if len(data['new_password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return data
    

