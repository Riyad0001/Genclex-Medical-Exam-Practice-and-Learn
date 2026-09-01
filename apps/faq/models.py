from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class FAQCategory(models.Model):
	"""
	Represents a FAQ category/section (e.g. "Getting Started", "Pricing & Plans").
	"""
	name = models.CharField(max_length=200)
	icon = models.CharField(
		max_length=50,
		blank=True,
		help_text="Icon identifier for the frontend (e.g. 'play', 'dollar').",
	)
	description = models.CharField(
		max_length=500,
		blank=True,
		help_text="Short subtitle shown below the category name.",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["created_at"]
		verbose_name = "FAQ Category"
		verbose_name_plural = "FAQ Categories"

	def __str__(self):
		return self.name


class FAQItem(models.Model):
	"""
	A single question-answer pair belonging to a category.
	"""
	category = models.ForeignKey(
		FAQCategory,
		on_delete=models.CASCADE,
		related_name="items",
	)
	question = models.CharField(max_length=500)
	answer = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["created_at"]
		verbose_name = "FAQ Item"
		verbose_name_plural = "FAQ Items"

	def __str__(self):
		return self.question


class Page(models.Model):
	"""
	A generic content page (e.g. Terms & Conditions, Privacy Policy).
	Content is managed via rich text editor in the admin panel.
	"""
	title = models.CharField(max_length=300)
	slug = models.SlugField(
		max_length=300,
		unique=True,
		help_text="URL-friendly identifier (e.g. 'terms-and-conditions').",
	)
	content = CKEditor5Field("Content", config_name="extends")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["title"]
		verbose_name = "Page"
		verbose_name_plural = "Pages"

	def __str__(self):
		return self.title
