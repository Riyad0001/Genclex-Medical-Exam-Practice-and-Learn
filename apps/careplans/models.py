from django.conf import settings
from django.db import models


class CarePlanHistory(models.Model):
    """
    Stores each generated or edited care plan for a specific user.

    Each POST to /care-plans/ or /care-plans/edit/ creates a new record,
    giving every user a full history of their plans.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="care_plan_history",
    )
    title = models.CharField(max_length=255, default="Care Plan")
    # Full care plan JSON stored as returned by services.generate_care_plan / edit_care_plan
    care_plan = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Care Plan History"
        verbose_name_plural = "Care Plan Histories"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.title} ({self.created_at:%Y-%m-%d})"

    @property
    def subtitle(self) -> str:
        """Extract subtitle from metadata for display."""
        return self.care_plan.get("metadata", {}).get("subtitle", "")
