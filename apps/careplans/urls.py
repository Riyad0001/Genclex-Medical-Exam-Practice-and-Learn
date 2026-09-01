from django.urls import path

from . import views

app_name = "careplans"

urlpatterns = [
    # Health check
    path("health/", views.HealthView.as_view(), name="health"),

    # Core generation / edit (stateless, but saves history when authenticated)
    path("care-plans/", views.CarePlanCreateView.as_view(), name="care-plans-create"),
    path("care-plans/edit/", views.CarePlanEditView.as_view(), name="care-plans-edit"),
    path("care-plans/affected-sections/", views.AffectedSectionsView.as_view(), name="care-plans-affected-sections"),

    # User-specific history
    path("care-plans/history/", views.CarePlanHistoryListView.as_view(), name="care-plans-history-list"),
    path("care-plans/history/<int:pk>/", views.CarePlanHistoryDetailView.as_view(), name="care-plans-history-detail"),

    # HTML test page
    path("care-plans/test/", views.care_plan_test_page, name="test-page"),
]
