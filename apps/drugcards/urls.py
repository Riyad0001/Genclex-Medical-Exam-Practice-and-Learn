from django.urls import path

from . import views

urlpatterns = [
    path("test-drugs/", views.index, name="index"),
    path("quick-picks/", views.api_quick_picks, name="api_quick_picks"),
    path("generate/", views.DrugCardGenerateView.as_view(), name="api_generate"),
    path("cache/clear/", views.api_clear_cache, name="api_clear_cache"),
    path("health/", views.api_health, name="api_health"),

    # User-specific history
    path("drug-card/history/", views.DrugCardHistoryListView.as_view(), name="drug-card-history-list"),
    path("drug-card/history/<int:pk>/", views.DrugCardHistoryDetailView.as_view(), name="drug-card-history-detail"),
]
