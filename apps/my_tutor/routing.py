from django.urls import re_path
from .consumers import MedicalTutorConsumer

websocket_urlpatterns = [
    re_path(r'ws/tutor/chat/$', MedicalTutorConsumer.as_asgi()),
]
