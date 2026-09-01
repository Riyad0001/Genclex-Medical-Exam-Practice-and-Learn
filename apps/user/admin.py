from django.contrib import admin

from apps.user.models import User, UserProfile

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'profile_photo', 'is_active', 'is_staff','otp_verified', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')
    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {
            'fields': ('email', 'password','otp_verified')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'profile_photo')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'university', 'country', 'terms_accepted', 'privacy_accepted')
    search_fields = ('user__email', 'program__name', 'university', 'country__name')
    list_filter = ('program__name', 'country__name', 'terms_accepted', 'privacy_accepted')






# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import User, BlacklistedAccessToken


# class UserAdmin(BaseUserAdmin):
#     ordering = ['-date_joined']
#     list_display = ['email', 'is_active', 'is_staff', 'otp_verified']
#     search_fields = ['email']

#     readonly_fields = ['date_joined']

#     fieldsets = (
#         (None, {
#             'fields': ('email', 'password')
#         }),
#         ('Personal Info', {
#             'fields': ('first_name', 'last_name')
#         }),
#         ('Verification', {
#             'fields': ('otp', 'otp_exp', 'otp_verified')
#         }),
#         ('Permissions', {
#             'fields': ('is_active', 'is_staff', 'is_superuser')
#         }),
#         ('Reset Token', {
#             'fields': ('reset_token', 'reset_token_exp')
#         }),
#         ('Important Dates', {
#             'fields': ('date_joined',)
#         }),
#     )

#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password1', 'password2'),
#         }),
#     )


# admin.site.register(User, UserAdmin)
