from django.urls import path

from .views import DiagnosticSaveAPIView, ECGAPIView, ECGSaveAPIView, DiagnosticAPIView, DosageAPIView, DosageSaveAPIView


urlpatterns = [
    path('ecg/', ECGAPIView.as_view()),         
    path('ecg/<int:pk>/', ECGAPIView.as_view()), 
    path('ecg-saved/', ECGSaveAPIView.as_view()),


    # Diagnostic URLs
    path('diagnostic/', DiagnosticAPIView.as_view()),
    path('diagnostic/<int:pk>/', DiagnosticAPIView.as_view()),
    path('diagnostic-saved/', DiagnosticSaveAPIView.as_view()),
   

    # Dosage URLs
    path('dosage/', DosageAPIView.as_view()),
    path('dosage/<int:pk>/', DosageAPIView.as_view()),
    path('dosage-saved/', DosageSaveAPIView.as_view()),
]
