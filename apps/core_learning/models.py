from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
##Study Material Models

LEARNING_PAGES = (
    ("study_notes", "Study Notes"),
    ("body_system", "Body System"),
    ("dosage_calcuation", "Dosage Calculation"),
    ("diagonstic_test", "Diagnostic Test"),
    ("ecg", "ECG"),
    ("stem_toons", "STEM Toons"),
    ("nursing_assessment", "Nursing Assessment"),
    ("cheat_sheet", "Cheat Sheet"),
)


class LearningContentIcon(models.Model):
    icon = models.FileField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "learning icon {self.id}"

class LearningContentColor(models.Model):
    color = models.CharField(max_length=7, default="#000000") 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.color

class Library(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="library")
    name = models.CharField(max_length=255, unique=True)
    icon = models.ForeignKey(LearningContentIcon, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name", "created_at"]

    def __str__(self):
        return self.name


class LearningCategory(models.Model):
    topic = models.CharField(max_length=255, choices=LEARNING_PAGES)
    title = models.CharField(max_length=255, default="Default")
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cover = models.ImageField(upload_to='category_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("topic", "title")
        ordering = ["id"]
    def __str__(self):
    #     if self.title.lower() == "default":
    #         return f"{self.title} ({self.topic})"
        return f"{self.title} ({self.topic})"


class LearningContent(models.Model):
    category = models.ForeignKey(
        LearningCategory,
        on_delete=models.CASCADE,
        related_name="contents"
    )
    content_name = models.CharField(max_length=255)
    content_file = models.FileField(upload_to='category_contents/', null=True, blank=True)
    content_cover = models.ImageField(upload_to='content_covers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.content_name


class SavedNotes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name="notes")
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name="saved_notes")
    # notes = models.TextField(blank=True, null=True) # for future extension
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "content", "library")
        ordering = ["created_at"]

    def __str__(self):
        return f"Notes by {self.user} for {self.content.content_name}"


class LearningProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    content = models.ForeignKey(LearningContent, on_delete=models.CASCADE, related_name="progress")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "content")
        ordering = ["completed_at"]

    def __str__(self):
        return f"Progress of {self.user} for {self.content.content_name}"



