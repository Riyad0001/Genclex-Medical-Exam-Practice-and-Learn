from django.contrib import admin

from unfold.admin import ModelAdmin

from .models import FAQCategory, FAQItem, Page


class FAQItemInline(admin.TabularInline):
	model = FAQItem
	extra = 1
	fields = ("question", "answer")


@admin.register(FAQCategory)
class FAQCategoryAdmin(ModelAdmin):
	list_display = ("name", "updated_at")
	search_fields = ("name",)
	inlines = [FAQItemInline]


@admin.register(FAQItem)
class FAQItemAdmin(ModelAdmin):
	list_display = ("question", "category", "updated_at")
	list_filter = ("category",)
	search_fields = ("question", "answer")


@admin.register(Page)
class PageAdmin(ModelAdmin):
	list_display = ("title", "slug", "updated_at")
	search_fields = ("title",)
	prepopulated_fields = {"slug": ("title",)}
