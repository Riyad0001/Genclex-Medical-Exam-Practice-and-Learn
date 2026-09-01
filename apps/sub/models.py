from django.conf import settings
User=settings.AUTH_USER_MODEL
from django.db import models


class Plan(models.Model):
    INTERVAL_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_title = models.CharField(max_length=150, blank=True)
    duration_label = models.CharField(max_length=50, blank=True)
    price_label = models.CharField(max_length=50, blank=True)
    price_sub_label = models.CharField(max_length=50, blank=True)
    billing_note = models.CharField(max_length=200, blank=True)
    badge_text = models.CharField(max_length=100, blank=True)
    cta_text = models.CharField(max_length=100, blank=True)
    features = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False)
    trial_days = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"


class Subscription(models.Model):
    PACKAGE_CHOICES = [("package-1", "Package 1")]
    BILLING_CHOICES = [("monthly", "Monthly"), ("yearly", "Yearly")]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name="subscriptions")
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    package = models.CharField(max_length=20, choices=PACKAGE_CHOICES, default="package-1")
    billing_interval = models.CharField(max_length=10, default="monthly")
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)

    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.user.email + " - " + self.package + " (" + self.billing_interval + ")"

