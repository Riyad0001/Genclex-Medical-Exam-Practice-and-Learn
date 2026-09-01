from django.urls import path

from .views import (
    ConceptMapDetailView,
    ConceptMapGenerateView,
    ConceptMapVisualizerView,
    ConceptMapListView,
    ConceptMapSelectView,
    ConceptMapDeleteView,
    ConceptMapClearView,
    ConceptMapImportView,
)

app_name = "cara"

urlpatterns = [
    # Visualizer frontend UI page
    path("concept-map/visualizer/", ConceptMapVisualizerView.as_view(), name="concept-map-visualizer"),

    # GET -> loads the user's current concept map; PUT -> saves manual edits
    path("concept-map/", ConceptMapDetailView.as_view(), name="concept-map-detail"),

    # POST {"prompt": "..."} -> generate concept map using AI
    path("concept-map/generate/", ConceptMapGenerateView.as_view(), name="concept-map-generate"),

    # GET -> list all user maps; POST -> create a new blank map
    path("concept-maps/", ConceptMapListView.as_view(), name="concept-map-list"),

    # POST -> select/load a map by ID
    path("concept-maps/<int:pk>/select/", ConceptMapSelectView.as_view(), name="concept-map-select"),

    # DELETE -> delete a specific map by ID
    path("concept-maps/<int:pk>/", ConceptMapDeleteView.as_view(), name="concept-map-delete"),

    # DELETE -> clear all maps of the user
    path("concept-maps/clear/", ConceptMapClearView.as_view(), name="concept-map-clear"),

    # POST -> import map from JSON
    path("concept-maps/import/", ConceptMapImportView.as_view(), name="concept-map-import"),
]

