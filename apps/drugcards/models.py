from django.conf import settings
from django.db import models


class DrugCardHistory(models.Model):
    """
    Stores each generated drug card for a specific user.

    Every successful POST to /api/drugcards/generate/ creates a new record,
    giving every user a full history of their generated drug cards.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="drug_card_history",
    )
    drug_name = models.CharField(max_length=255)
    # Full drug card JSON as returned by drug_card_generator.get_drug_card()
    card_data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Drug Card History"
        verbose_name_plural = "Drug Card Histories"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.drug_name} ({self.created_at:%Y-%m-%d})"
