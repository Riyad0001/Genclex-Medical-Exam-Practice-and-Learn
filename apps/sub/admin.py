from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import *

@admin.register(Plan)
class PlanAdmin(ModelAdmin):
    pass

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    pass





