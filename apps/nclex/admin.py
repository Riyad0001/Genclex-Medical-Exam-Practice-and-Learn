# from django.contrib import admin
# from apps.nclex.models import CalculatorHistory, Question, Category, Option, Result, Exam


# @admin.register(CalculatorHistory)
# class CalculatorHistoryAdmin(admin.ModelAdmin):
#     list_display = ('num1', 'num2', 'operation', 'expression', 'result', 'created_at')
#     search_fields = ('expression', 'operation')
#     list_filter = ('operation', 'created_at')


# @admin.register(Exam)
# class ExamAdmin(admin.ModelAdmin):

#     list_display = (
#         'id',
#         'title',
#         'user',
#         'level',
#         'status',
#         'is_lock',         
#         'exam_duration',
#         'total_questions',
#         'completed_exam',
#         'started_at',
#         'create_at',
    
    
#     )

#     list_filter = (
#         'level',
#         'status',
#         'completed_exam',
#         'is_lock',             
#         'started_at',
#         'create_at',
        
#     )

#     search_fields = (
#         'title',
#         'description',
#         'exam_id',
#         'user__username',
#         'user__email',
#     )

#     ordering = ('-create_at',)

#     readonly_fields = (
#         'create_at',
#         'started_at',
#     )

#     fieldsets = (
#         ("Basic Info", {
#             "fields": (
#                 'user',
#                 'title',
#                 'description',
#                 'level',
#             )
#         }),
#         ("Exam Details", {
#             "fields": (
#                 'exam_duration',
#                 'total_questions',
#                 'exam_id',
#             )
#         }),
#         ("Status Info", {
#             "fields": (
#                 'status',
#                 'completed_exam',
#                 'is_lock',         
#                 'started_at',
#             )
#         }),
#         ("System Info", {
#             "fields": (
#                 'create_at',
#             )
#         }),
#     )

# class OptionInline(admin.TabularInline):
#     model = Option
#     extra = 4


# @admin.register(Question)
# class QuestionAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'exam_question',
#         'category',
#         'is_multiple',
#         'is_flagged',
#         'is_skipped',
#         'subcategory',
#         'explanation',
#         'submit_at',
#     )
   
#     list_filter = (
#         'exam_question',
#         'category',
#         'is_multiple',
#         'is_flagged',
#         'is_skipped',
#         'submit_at',
#     )

#     search_fields = (
#         'text',
#         'exam__title',
#         'category__name',
#     )

#     ordering = ('-submit_at',)

#     inlines = [OptionInline]


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')
#     search_fields = ('name',)


# @admin.register(Option)
# class OptionAdmin(admin.ModelAdmin):
   
#     list_display = (
#         'id',
#         'mcq_option',
#         'question',
#         'is_correct',
#         'is_select',
#     )

#     list_filter = (
#         'is_correct',
#         'is_select',
#         'question',
#         'mcq_option',
#     )

#     search_fields = (
#         'text',
#         'question__text',
#     )

#     ordering = ('question',)

# @admin.register(Result)
# class ResultAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'user',
#         'exam',
#         'score',
#         # 'explanation_image',
#         'finished_date',
#         'create_at',
#     )

#     list_filter = (
#         'exam',
#         'user',
#         # 'explanation_image',
#         'finished_date',
#         'create_at',
#     )

#     search_fields = (
#         'user__username',
#         'exam__title',
#         'score',
#     )

#     readonly_fields = (
#         'create_at',
#         'finished_date',
#     )

#     ordering = ('-create_at',)
