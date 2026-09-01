from rest_framework import serializers

from .models import FAQCategory, FAQItem, Page


class FAQItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = FAQItem
		fields = [
			"id",
			"question",
			"answer",
		]


class FAQCategoryDetailSerializer(serializers.ModelSerializer):
	"""Serialises a category WITH its nested active FAQ items."""

	items = FAQItemSerializer(many=True, read_only=True)

	class Meta:
		model = FAQCategory
		fields = [
			"id",
			"name",
			"icon",
			"description",
			"items",
		]


class PageSerializer(serializers.ModelSerializer):
	class Meta:
		model = Page
		fields = [
			"id",
			"title",
			"slug",
			"content",
			"updated_at",
		]
