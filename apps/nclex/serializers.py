from rest_framework import serializers
from .models import CalculatorHistory, Question, Option, Result, Exam

#--------------------------------- Calculative Serializer ----------------------------------- #
class CalculatorSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["calculate", "clear"])
    num1 = serializers.IntegerField(required=False)
    num2 = serializers.IntegerField(required=False)
    operation = serializers.ChoiceField(
        choices=["add", "sub", "mul", "div"],
        required=False
    )

class CalculatorHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorHistory
        fields = '__all__'


# ------------------------------ Option Serializer ------------------------------------- #
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'mcq_option','explanation_image']

# ------------------------------ Questions Serializer -----------------------------------#
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    category = serializers.CharField(source='category.name')

    class Meta:
        model = Question
        fields = ['id', 'exam_question', 'is_multiple', 'category', 'options']


# ---------------------------- User Result Serializer ----------------------------------#
class UserResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = '__all__'

# ---------------------------- Exam Completed Serializer -------------------------------#
class ExamCompleteSerializer(serializers.ModelSerializer):
    percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Exam
        fields = [
            'id',
            'title',
            'description',
            'level',
            'exam_duration',
            'total_questions',
            'exam_id',
            'started_at',
            'completed_exam',
            'status',
            'create_at',
            'is_lock',
            'percentage'
        ]
    
# --------------------------------- Next Exam Serializer ------------------------------------#
class NextExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title', 'status', 'is_lock']


# ----------------------------------- Exam Questions Details Serializer ----------------------------#
class ExamQuestionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    category = serializers.CharField()
    subcategory = serializers.CharField(allow_null=True)

    question = serializers.CharField()

    is_correct = serializers.BooleanField()

    explanation = serializers.CharField(allow_null=True)
    image = serializers.CharField(allow_null=True)

