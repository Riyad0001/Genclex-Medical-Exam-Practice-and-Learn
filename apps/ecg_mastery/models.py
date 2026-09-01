from django.db import models
from requests import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.sub.models import User


class ECGPage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    html_file = models.FileField(upload_to='ecg_html/')
    is_saved = models.BooleanField(default=False)
   
    
    def __str__(self):
        return self.title
    

class Diagnostic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    html_file = models.FileField(upload_to='diagnostic_html/')
    title_logo = models.ImageField(upload_to='title_logo/', null=True, blank=True)
    is_saved = models.BooleanField(default=False)
 

    def __str__(self):
        return self.title


class Dosage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    html_file = models.FileField(upload_to='dosage_html/')
    title_logo = models.ImageField(upload_to='title_logo/', null=True, blank=True)
    is_saved = models.BooleanField(default=False)

    def __str__(self):
       return str(self.title or f"Dosage #{self.pk}")
    

