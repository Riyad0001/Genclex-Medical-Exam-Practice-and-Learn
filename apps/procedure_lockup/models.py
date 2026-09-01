from django.db import models
from django.conf import settings

class ProcedureModule(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    procedure_html = models.FileField(upload_to='procedure_html/', null=True, blank=True)



class Lecture_Notes(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lecture_notes"
    )
    title = models.CharField(max_length=255)
    user_html = models.TextField()
    formatted_html = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


