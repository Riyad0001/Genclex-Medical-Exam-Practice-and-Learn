from django.urls import path
from .views import VoiceSessionView

urlpatterns = [
    path('tutor/voice/session/', VoiceSessionView.as_view(), name='tutor_voice_session'),
]
