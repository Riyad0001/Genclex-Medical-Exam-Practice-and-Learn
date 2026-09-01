from django.urls import path
from .views import (
    LandingPageAPIView,
    LandingHeroListCreateAPIView,
    LandingHeroDetailAPIView,
    LandingStatsBannerListCreateAPIView,
    LandingStatsBannerDetailAPIView,
    AITutorSpotlightListCreateAPIView,
    AITutorSpotlightDetailAPIView,
    LandingFeatureListCreateAPIView,
    LandingFeatureDetailAPIView,
    PillarsSectionListCreateAPIView,
    PillarsSectionDetailAPIView,
    AIToolCardListCreateAPIView,
    AIToolCardDetailAPIView,
)

urlpatterns = [
    path("cms/landing-page/", LandingPageAPIView.as_view(), name="cms-landing-page"),
    path("cms/hero/", LandingHeroListCreateAPIView.as_view(), name="cms-hero-list-create"),
    path("cms/hero/<int:pk>/", LandingHeroDetailAPIView.as_view(), name="cms-hero-detail"),
    path("cms/stats/", LandingStatsBannerListCreateAPIView.as_view(), name="cms-stats-list-create"),
    path("cms/stats/<int:pk>/", LandingStatsBannerDetailAPIView.as_view(), name="cms-stats-detail"),
    path("cms/ai-tutor/", AITutorSpotlightListCreateAPIView.as_view(), name="cms-ai-tutor-list-create"),
    path("cms/ai-tutor/<int:pk>/", AITutorSpotlightDetailAPIView.as_view(), name="cms-ai-tutor-detail"),
    path("cms/features/", LandingFeatureListCreateAPIView.as_view(), name="cms-feature-list-create"),
    path("cms/features/<int:pk>/", LandingFeatureDetailAPIView.as_view(), name="cms-feature-detail"),
    path("cms/pillars/", PillarsSectionListCreateAPIView.as_view(), name="cms-pillars-list-create"),
    path("cms/pillars/<int:pk>/", PillarsSectionDetailAPIView.as_view(), name="cms-pillars-detail"),
    path("cms/ai-tools/", AIToolCardListCreateAPIView.as_view(), name="cms-ai-tools-list-create"),
    path("cms/ai-tools/<int:pk>/", AIToolCardDetailAPIView.as_view(), name="cms-ai-tools-detail"),
]
