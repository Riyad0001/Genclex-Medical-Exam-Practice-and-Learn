# from unfold.admin import ModelAdmin
# from django.contrib import admin
# from apps.ecg_mastery.models import ECGPage, Diagnostic, Dosage
# from django.utils.html import format_html

# @admin.register(ECGPage)
# class ECGPageAdmin(ModelAdmin):   
#     list_display = ('id', 'title', 'user', 'is_saved', 'html_file')
#     list_filter = ('is_saved', 'user')
#     search_fields = ('title', 'user__email', 'user__username')
#     readonly_fields = ('id',)

#     fieldsets = (
#         ("Basic Info", {
#             "fields": ("user", "title")
#         }),
#         ("File Info", {
#             "fields": ("html_file",)
#         }),
#         ("Status", {
#             "fields": ("is_saved",)
#         }),
#     )


# @admin.register(Diagnostic)
# class DiagnosticAdmin(ModelAdmin): 
#     list_display = ('id', 'title', 'user', 'is_saved', 'html_file', 'title_logo')
#     list_filter = ('is_saved', 'user')
#     search_fields = ('title', 'user__email', 'user__username')
#     readonly_fields = ('id',)

#     fieldsets = (
#         ("Basic Info", {
#             "fields": ("user", "title", "title_logo")
#         }),
#         ("File Info", {
#             "fields": ("html_file",)
#         }),
#         ("Status", {
#             "fields": ("is_saved",)
#         }),
#     )


# @admin.register(Dosage)
# class DosageAdmin(ModelAdmin): 
#     list_display = ('id', 'title', 'user', 'is_saved', 'html_file', 'title_logo')
#     list_filter = ('is_saved', 'user')
#     search_fields = ('title', 'user__email', 'user__username')
#     readonly_fields = ('id',)

#     fieldsets = (
#         ("Basic Info", {
#             "fields": ("user", "title", "title_logo")
#         }),
#         ("File Info", {
#             "fields": ("html_file",)
#         }),
#         ("Status", {
#             "fields": ("is_saved",)
#         }),
#     )