from django.urls import path
from .views import (
    ModuleAPIView,
    VideoDetailsAPIView,
    VideoProgressCreateUpdateView,
    VideoProgressView,
    LibraryDashboardAPIView
  
)

urlpatterns = [
    path("module/", ModuleAPIView.as_view(), name="module-list"),
    path("module/<int:pk>/", ModuleAPIView.as_view(), name="module-detail"),
    path("video/<int:pk>/",VideoDetailsAPIView.as_view(),name="video-details"),
    path("video/progress/<int:video_id>/", VideoProgressCreateUpdateView.as_view()),   # tracking vedio time duration 

    path("vedio_progress/", VideoProgressView.as_view(), name="module-list"),   # vedio progress means watching this vedio and in progress and no start


    path("dashboard-vedio-progress/", LibraryDashboardAPIView.as_view(), name="dashboard-vedio-progress"),   
] 

