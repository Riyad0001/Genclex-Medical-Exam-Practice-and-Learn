from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType

class Module(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True) 
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    def __str__(self):
        return self.name


class VideoContent(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='vedio')
    serial_number = models.PositiveIntegerField(unique=True, editable=False)
    title = models.CharField(max_length=100, blank=True, null=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    video_url = models.FileField(upload_to="videos/", blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)

    
    def save(self, *args, **kwargs):
        if not self.serial_number:
            last = VideoContent.objects.order_by('-serial_number').first()
            self.serial_number = (last.serial_number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)


class Resources(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="video_content_resources",
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="lesson_source_resources",
        blank=True,
        null=True,
    )
    source_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    source_object = GenericForeignKey(
        'source_content_type',
        'source_object_id'
    )

    def __str__(self):
       return str(self.source_object) if self.source_object else f"{self.content_type} - {self.object_id}"


class VedioProgress(models.Model):
   
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_progress"
    )

    vedio_content = models.ForeignKey(
        VideoContent,
        on_delete=models.CASCADE,
        related_name="progresses"
    )

    total_duration = models.PositiveIntegerField()
    current_duration = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "vedio_content")

    def __str__(self):
        return f"{self.user} - {self.vedio_content.title}"

