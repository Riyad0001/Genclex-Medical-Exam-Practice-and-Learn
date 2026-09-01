from django.urls import path
from . import views 

urlpatterns = [
    path("learning/<str:topic>/", views.LearningContentView.as_view()),
    path(
        "library/content/<int:content_id>/", views.LearningContentView.as_view()
    ),  # content details view
    path("save-note/", views.SavedNotesView.as_view()),

    path("library/", views.LibraryView.as_view()),
    path(
        "library/<int:pk>/", views.LibraryDetailView.as_view()
    ),  # library rename and delete api
    
    path("mark-as-completed/<int:content_id>/", views.MarkAsCompletedAPIView.as_view()),
    path("icons/", views.LearningIconAPIView.as_view()),
    
    path("color/", views.LibraryColorAPIView.as_view()),
    
    path("learning/category/<int:category_id>/", views.LearningContentDetailView.as_view()),
    path("learning/content/<int:content_id>/", views.LearningContentDetailView.as_view()),
    path("study-notes-dashboard/", views.LearningDashboardAPIView.as_view()),                     # study notes dashboard


    
]
