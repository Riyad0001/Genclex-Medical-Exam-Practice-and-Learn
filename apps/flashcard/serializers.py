from rest_framework import serializers
from .models import Category, Sub_Category, Card, Question


class QuestionSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='question_img', read_only=True)
    ans_image = serializers.ImageField(source='ans_img', read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "image",
            "answer_text",
            "ans_image",
            "is_easy"
        ]


class CardSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Card
        fields = ["id", "name", "questions"]


class SubCategorySerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = Sub_Category
        fields = ["id", "name", "cards"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "subcategories"]