from django.db import models
from django.conf import settings
from django.utils import timezone


class NCLEXCategory(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class NCLEXTopic(models.Model):
    category = models.ForeignKey(NCLEXCategory,on_delete=models.CASCADE,related_name="topics",)
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title


class NCLEXSubtopic(models.Model):
    topic = models.ForeignKey(NCLEXTopic, on_delete=models.CASCADE,related_name="subtopics",)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=255)

    def __str__(self):
        return self.title


class QuestionType(models.TextChoices):
    RADIO = "radio", "Radio"
    MULTIPLE = "multiple", "Multiple Select"
    ORDER = "order", "Drag Order"
    INPUT = "input", "Input"
    HIGHLIGHT = "highlight", "Highlight"

class NCLEXQuestion(models.Model):

    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ]
   
    category = models.ForeignKey(NCLEXCategory,on_delete=models.CASCADE,related_name="questions", db_index=True)
    topic = models.ForeignKey(NCLEXTopic,on_delete=models.CASCADE,related_name="questions", db_index=True)
    subtopic = models.ForeignKey(NCLEXSubtopic,on_delete=models.CASCADE,related_name="questions", db_index=True)
    question = models.TextField(max_length=255)
    explanation = models.FileField(upload_to='explanations/', null=True, blank=True)
    level = models.CharField(max_length=20,choices=LEVEL_CHOICES)
    type = models.CharField(max_length=20,choices=QuestionType.choices,)
    passage = models.TextField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict,blank=True)
    note = models.TextField(max_length=255, blank=True, null=True)
    avg_solve_percent = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):    
        return self.question


class QuestionOption(models.Model):
    question = models.ForeignKey(NCLEXQuestion,on_delete=models.CASCADE,related_name="answers",)
    text = models.TextField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    is_correct = models.BooleanField(default=False)
    extra_data = models.JSONField(
        default=dict,
        blank=True,
    )
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question.question


class NCLEXExam(models.Model):
    LEVEL_CHOICES = [
        ('Foundational', 'Foundational'),
        ('Progressive', 'Progressive'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    tag = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Start Here, Up next, Pass Predictor")
    order = models.PositiveIntegerField(default=1, help_text="Sequence order (1 to 5)")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Foundational')
    total_question = models.PositiveIntegerField(default=85)
    time_limit_mins = models.PositiveIntegerField(default=150, help_text="Time limit in minutes")
    questions = models.ManyToManyField(NCLEXQuestion, blank=True, related_name="nclex_exams")
    blueprint = models.JSONField(default=dict, blank=True, help_text="Category distribution blueprint for 85 items")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "NCLEX Exam"
        verbose_name_plural = "NCLEX Exams"

    def __str__(self):
        return f"{self.title} (Exam {self.order})"


# Alias for backward compatibility if any legacy code imports NCLEXQBank
NCLEXQBank = NCLEXExam


PRACTICE_MODE_CHOICES = [
    ("tutorial", "Tutorial"),
    ("test", "Test"),
]

class PracticeSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="exam_sessions",)
    total_question = models.PositiveIntegerField(blank=True, null=True)
    practice_mode = models.CharField(max_length=20,choices=PRACTICE_MODE_CHOICES)
    topic = models.ForeignKey(NCLEXTopic,on_delete=models.SET_NULL,related_name="practice_sessions",null=True,blank=True)
    subtopic = models.ForeignKey(NCLEXSubtopic,on_delete=models.SET_NULL,related_name="practice_sessions",null=True,blank=True)
    question_set = models.ManyToManyField(NCLEXQuestion, blank=True, related_name="practice_sessions")

    total_correct = models.PositiveIntegerField(default=0)
    total_incorrect = models.PositiveIntegerField(default=0)
    total_skipped = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return f"{self.user.email}"


class PracticeQuestionResult(models.Model):
    session = models.ForeignKey(PracticeSession,on_delete=models.CASCADE,related_name="question_results",)
    question = models.ForeignKey(NCLEXQuestion,on_delete=models.CASCADE)
    answer = models.ForeignKey(QuestionOption,on_delete=models.SET_NULL,related_name="question_results",null=True,blank=True)
    is_correct = models.BooleanField(default=False)
    extra_data = models.JSONField(
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("session", "question")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Practice Question Result for {self.session.user.email}"


class NCLEXExamResult(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="nclex_exam_results",
    )
    exam = models.ForeignKey(
        NCLEXExam,
        on_delete=models.CASCADE,
        related_name="user_results",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
    )
    score = models.FloatField(default=0.0, help_text="Percentage score")
    total_question = models.PositiveIntegerField(default=85)
    total_correct = models.PositiveIntegerField(default=0)
    total_incorrect = models.PositiveIntegerField(default=0)
    total_skipped = models.PositiveIntegerField(default=0)
    assigned_question_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of question IDs assigned to this unique attempt",
    )
    flagged_question_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of question IDs currently flagged by the student",
    )
    current_index = models.PositiveIntegerField(
        default=0,
        help_text="Current active question index in the exam",
    )
    analytics_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached comprehensive post-exam diagnostic performance analysis",
    )
    is_unlocked = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'exam')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.exam.title} ({self.status})"

    def get_remaining_seconds(self):
        if self.status == "completed":
            return 0
        if not self.started_at:
            return self.exam.time_limit_mins * 60
        elapsed = (timezone.now() - self.started_at).total_seconds()
        total_allowed = self.exam.time_limit_mins * 60
        remaining = int(total_allowed - elapsed)
        return max(0, remaining)

    def is_time_expired(self):
        return self.get_remaining_seconds() <= 0


class Exam_question_result(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_question_results",
    )
    exam_result = models.ForeignKey(
        NCLEXExamResult,
        on_delete=models.CASCADE,
        related_name="question_results",
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(
        NCLEXExam,
        on_delete=models.CASCADE,
        related_name="exam_question_results",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        NCLEXCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    subtopic = models.ForeignKey(
        NCLEXSubtopic,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    question = models.ForeignKey(
        NCLEXQuestion,
        on_delete=models.CASCADE,
        related_name="exam_question_results",
    )
    answer = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_question_results",
    )
    selected_answer = models.ManyToManyField(
        QuestionOption,
        blank=True,
        related_name="selected_in_exam_results",
    )
    selected_text = models.TextField(blank=True, null=True)
    selected_highlight = models.JSONField(default=list, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    is_correct = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.question.question[:30]}"




