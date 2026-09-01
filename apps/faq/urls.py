from django.urls import path

from .views import FAQListAPIView, PageDetailAPIView

urlpatterns = [
	path("faqs/", FAQListAPIView.as_view(), name="faq-list"),
	path("pages/<slug:slug>/", PageDetailAPIView.as_view(), name="page-detail"),
]
