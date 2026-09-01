from django.db import models
from django.conf import settings


class Exam(models.Model):
    LEVEL_CHOICES = [
        ('foundational', 'Foundational'),
        ('progressive', 'Progressive'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    STATUS_CHOICE = [
        ('completed', 'completed'),
        ('up_next', 'up_next'),
        ('locked', 'locked'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    exam_duration = models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True) 
    total_questions = models.IntegerField(blank=True, null=True)
    exam_id = models.IntegerField(blank=True,null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_exam = models.BooleanField(default=False)
    status = models.CharField(max_length=20,blank=True,null=True, choices=STATUS_CHOICE)
    create_at = models.DateTimeField(blank=True, null=True)
    is_lock = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    

# --------------------------Result-----------------------------------------#
class Result(models.Model):
   user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
   exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
   correct_ans = models.CharField(max_length=50, blank=True, null=True)
   Incorrect_ans=models.CharField(max_length=50, blank=True, null=True)
   flag_question=models.CharField(max_length=50, blank=True, null=True)
   skip_question=models.CharField(max_length=50, blank=True, null=True)
   subcategory_view= models.CharField(max_length=50, blank=True, null=True)
   explanation_view = models.TextField(blank=True, null=True)  
   explanation_image_view = models.ImageField(upload_to='explanations/', null=True, blank=True)
   score= models.CharField(max_length=50, blank=True, null=True)
   finished_date = models.DateTimeField(blank=True, null=True)
   create_at = models.DateTimeField(blank=True, null=True)

#---------------------- Questions Category -----------------------------#
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

#-------------------------- Questions Types -----------------------------#
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    subcategory= models.CharField(max_length=50, blank=True, null=True)
    exam_question = models.TextField()
    explanation_image = models.ImageField(upload_to='explanations/', null=True, blank=True)
    explanation = models.TextField(blank=True, null=True) 
    is_multiple=models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False) 
    submit_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.exam)
    
#-------------------------------- Option -----------------------------------#
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    mcq_option = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    is_select = models.BooleanField(default=False)


    def __str__(self):
        return str(self.question)
    
# ---------------------------------------- Calculative --------------------------#
class CalculatorHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    num1 = models.IntegerField(null=True, blank=True)
    num2 = models.IntegerField(null=True, blank=True)
    operation = models.CharField(max_length=10, null=True, blank=True)
    expression = models.CharField(max_length=255, null=True, blank=True)
    result = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
