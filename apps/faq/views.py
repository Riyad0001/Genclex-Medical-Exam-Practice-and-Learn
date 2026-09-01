from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FAQCategory, Page
from .serializers import FAQCategoryDetailSerializer, PageSerializer


class FAQListAPIView(APIView):
	"""
	GET /api/faqs/
	Returns ALL categories with their FAQ items in one response.
	"""
	permission_classes = [AllowAny]

	def get(self, request):
		categories = FAQCategory.objects.prefetch_related("items").all()
		serializer = FAQCategoryDetailSerializer(categories, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)


class PageDetailAPIView(APIView):
	"""
	GET /api/pages/<slug>/
	Returns a single page by slug (e.g. 'terms-and-conditions', 'privacy-policy').
	"""
	permission_classes = [AllowAny]

	def get(self, request, slug):
		page = Page.objects.filter(slug=slug).first()
		if not page:
			return Response(
				{"detail": "Page not found."},
				status=status.HTTP_404_NOT_FOUND,
			)
		serializer = PageSerializer(page)
		return Response(serializer.data, status=status.HTTP_200_OK)
