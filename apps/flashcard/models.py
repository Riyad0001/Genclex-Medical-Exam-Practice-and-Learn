from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.name


class Sub_Category(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.name

class Card(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='cards')
    sub_category = models.ForeignKey(Sub_Category, on_delete=models.CASCADE, related_name='cards')
    name = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.name

class Question(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=50, blank=True, null=True)
    question_img = models.ImageField(upload_to='question_images/', blank=True, null=True)
    answer_text = models.CharField(max_length=255, blank=True, null=True)
    ans_img = models.ImageField(upload_to='answer_img/', blank=True, null=True)
    is_easy = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.question_text}"


class Progress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='results')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='progress')
    is_hard = models.BooleanField(default=False)
    is_easy = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.email} - {self.question.question_text} - {'Easy' if self.is_easy else 'Hard'}"









    



