from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Category,
    Sub_Category,
    Card,
    Question,
    Progress
)


# ----------------- CATEGORY -----------------
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

    fieldsets = (
        ('Category Information', {
            'fields': ('name',)
        }),
    )


# ----------------- SUB CATEGORY -----------------
@admin.register(Sub_Category)
class SubCategoryAdmin(ModelAdmin):
    list_display = ['id', 'name', 'category']
    search_fields = ['name', 'category__name']
    list_filter = ['category']

    autocomplete_fields = ['category']

    fieldsets = (
        ('Sub Category Information', {
            'fields': (
                'category',
                'name'
            )
        }),
    )


# ----------------- CARD -----------------
@admin.register(Card)
class CardAdmin(ModelAdmin):
    list_display = [
        'id',
        'name',
        'category',
        'sub_category'
    ]

    search_fields = [
        'name',
        'category__name',
        'sub_category__name'
    ]

    list_filter = [
        'category',
        'sub_category'
    ]

    autocomplete_fields = [
        'category',
        'sub_category'
    ]

    fieldsets = (
        ('Card Information', {
            'fields': (
                'category',
                'sub_category',
                'name'
            )
        }),
    )


# ----------------- QUESTION -----------------
@admin.register(Question)
class QuestionAdmin(ModelAdmin):

    list_display = [
        'id',
        'question_text',
        'card'
    ]

    search_fields = [
        'question_text',
        'card__name'
    ]

    list_filter = [
        'card'
    ]

    autocomplete_fields = [
        'card'
    ]

    fieldsets = (
        ('Question Information', {
            'fields': (
                'card',
                'question_text',
                'question_img',
                'answer_text',
                'ans_img',
                'is_easy'
            )
        }),
    )

# ----------------- PROGRESS -----------------
@admin.register(Progress)
class ProgressAdmin(ModelAdmin):

    list_display = [
        'id',
        'user',
        'question',
        'is_easy',
        'is_hard',
        'reviewed'
    ]

    search_fields = [
        'user__email',
        'question__question_text'
    ]

    list_filter = [
        'is_easy',
        'is_hard',
        'reviewed'
    ]

    autocomplete_fields = [
        'user',
        'question'
    ]

    fieldsets = (
        ('Progress Information', {
            'fields': (
                'user',
                'question',
                'is_easy',
                'is_hard',
                'reviewed'
            )
        }),
    )
