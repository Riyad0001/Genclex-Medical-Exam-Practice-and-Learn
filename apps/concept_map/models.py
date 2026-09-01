from django.conf import settings
from django.db import models


class NursingConceptMap(models.Model):
    """
    Ekjon user er "current" concept map state store kore.

    OneToOne rakha hoyeche karon original script e ekta shomoy e ekta hi
    "current_concept_map" state thake (create -> edit -> edit ... একই map),
    ঠিক jemon frontend e ekta chat session e ekta map build hoy.

    Jodi future e ekjon user er MULTIPLE saved maps (history/list) lagbe,
    tahole eta ForeignKey(user) + `is_active` boolean flag diye extend kora
    jabe — GET API tখন `is_active=True` wala ta return korবে.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="concept_maps",
    )
    title = models.CharField(max_length=255, default="Clinical Concept Map")
    is_current = models.BooleanField(default=True)

    # Visualizer exact shape e store kora hocche: nodes -> list[dict], edges -> list[dict]
    nodes = models.JSONField(default=list, blank=True)
    edges = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nursing Concept Map"
        verbose_name_plural = "Nursing Concept Maps"

    def __str__(self) -> str:
        return f"{self.user} — {self.title}"

    def to_dict(self) -> dict:
        """Exact same shape concept_map_visualizer.html / the AI service reads & returns."""
        return {"id": self.id, "title": self.title, "nodes": self.nodes, "edges": self.edges, "is_current": self.is_current}

    def apply_dict(self, data: dict) -> None:
        """Overwrite this row with a freshly generated/updated map dict."""
        self.title = data.get("title") or self.title
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])

    def save(self, *args, **kwargs):
        if self.is_current:
            # Deactivate other maps of this user
            NursingConceptMap.objects.filter(user=self.user, is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def subtitle(self) -> str:
        for node in self.nodes:
            if isinstance(node, dict) and node.get("category") == "Central":
                return node.get("label") or "Untitled"
        return "Untitled"

    @property
    def snippet(self) -> str:
        for node in self.nodes:
            if isinstance(node, dict) and node.get("category") == "Nursing Diagnosis":
                details = node.get("details") or ""
                details_clean = details.lstrip("•-* ").strip()
                if details_clean:
                    return f"• {details_clean[:40]}..." if len(details_clean) > 40 else f"• {details_clean}"
        for node in self.nodes:
            if isinstance(node, dict) and node.get("category") == "Central":
                details = node.get("details") or ""
                details_clean = details.lstrip("•-* ").strip()
                if details_clean:
                    return details_clean[:50] + "..." if len(details_clean) > 50 else details_clean
        return ""

