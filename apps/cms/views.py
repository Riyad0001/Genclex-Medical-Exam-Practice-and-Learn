from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *


class LandingPageAPIView(APIView):
    """
    GET /api/cms/landing-page/
    Returns full landing page content in a single aggregated response.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        hero = LandingHero.objects.filter(is_active=True).last()
        stats_banner = LandingStatsBanner.objects.filter(is_active=True).last()
        ai_tutor_spotlight = AITutorSpotlight.objects.filter(is_active=True).last()
        features = LandingFeature.objects.filter(is_active=True).order_by("order", "step_number")
        pillars = PillarsSection.objects.filter(is_active=True).last()
        ai_tools = AIToolCard.objects.filter(is_active=True).order_by("order")

        data = {
            "hero": LandingHeroSerializer(hero, context={"request": request}).data if hero else None,
            "stats_banner": LandingStatsBannerSerializer(stats_banner, context={"request": request}).data if stats_banner else None,
            "ai_tutor_spotlight": AITutorSpotlightSerializer(ai_tutor_spotlight, context={"request": request}).data if ai_tutor_spotlight else None,
            "features_header": {
                "title": "Everything You Need to Succeed in Nursing School",
                "subtitle": "Comprehensive tools engineered specifically for NCLEX prep and clinical practice.",
            },
            "features": LandingFeatureSerializer(features, many=True, context={"request": request}).data,
            "pillars": PillarsSectionSerializer(pillars, context={"request": request}).data if pillars else None,
            "ai_tools_header": {
                "title": "Powerful AI Tools for Nursing Students",
                "subtitle": "Everything you need to study, practice, and succeed in one place.",
            },
            "ai_tools": AIToolCardSerializer(ai_tools, many=True, context={"request": request}).data,
        }

        return Response(data, status=status.HTTP_200_OK)


class LandingHeroListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        heroes = LandingHero.objects.all()
        serializer = LandingHeroSerializer(heroes, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = LandingHeroSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LandingHeroDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return LandingHero.objects.get(pk=pk)
        except LandingHero.DoesNotExist:
            return None

    def get(self, request, pk):
        hero = self.get_object(pk)
        if not hero:
            return Response({"detail": "Hero section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingHeroSerializer(hero, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        hero = self.get_object(pk)
        if not hero:
            return Response({"detail": "Hero section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingHeroSerializer(hero, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        hero = self.get_object(pk)
        if not hero:
            return Response({"detail": "Hero section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingHeroSerializer(hero, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        hero = self.get_object(pk)
        if not hero:
            return Response({"detail": "Hero section not found."}, status=status.HTTP_404_NOT_FOUND)
        hero.delete()
        return Response({"message": "Hero section deleted successfully."}, status=status.HTTP_200_OK)


class LandingStatsBannerListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        stats = LandingStatsBanner.objects.all()
        serializer = LandingStatsBannerSerializer(stats, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = LandingStatsBannerSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AITutorSpotlightListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        spotlights = AITutorSpotlight.objects.all()
        serializer = AITutorSpotlightSerializer(spotlights, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = AITutorSpotlightSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LandingFeatureListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        features = LandingFeature.objects.all().order_by("order", "step_number")
        serializer = LandingFeatureSerializer(features, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = LandingFeatureSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LandingFeatureDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return LandingFeature.objects.get(pk=pk)
        except LandingFeature.DoesNotExist:
            return None

    def get(self, request, pk):
        feature = self.get_object(pk)
        if not feature:
            return Response({"detail": "Landing feature not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingFeatureSerializer(feature, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        feature = self.get_object(pk)
        if not feature:
            return Response({"detail": "Landing feature not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingFeatureSerializer(feature, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        feature = self.get_object(pk)
        if not feature:
            return Response({"detail": "Landing feature not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingFeatureSerializer(feature, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        feature = self.get_object(pk)
        if not feature:
            return Response({"detail": "Landing feature not found."}, status=status.HTTP_404_NOT_FOUND)
        feature.delete()
        return Response({"message": "Landing feature deleted successfully."}, status=status.HTTP_200_OK)


class PillarsSectionListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        pillars = PillarsSection.objects.all()
        serializer = PillarsSectionSerializer(pillars, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PillarsSectionSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PillarsSectionDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return PillarsSection.objects.get(pk=pk)
        except PillarsSection.DoesNotExist:
            return None

    def get(self, request, pk):
        pillar_section = self.get_object(pk)
        if not pillar_section:
            return Response({"detail": "Pillars section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PillarsSectionSerializer(pillar_section, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        pillar_section = self.get_object(pk)
        if not pillar_section:
            return Response({"detail": "Pillars section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PillarsSectionSerializer(pillar_section, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        pillar_section = self.get_object(pk)
        if not pillar_section:
            return Response({"detail": "Pillars section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PillarsSectionSerializer(pillar_section, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        pillar_section = self.get_object(pk)
        if not pillar_section:
            return Response({"detail": "Pillars section not found."}, status=status.HTTP_404_NOT_FOUND)
        pillar_section.delete()
        return Response({"message": "Pillars section deleted successfully."}, status=status.HTTP_200_OK)


class AIToolCardListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        tools = AIToolCard.objects.all().order_by("order")
        serializer = AIToolCardSerializer(tools, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        serializer = AIToolCardSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIToolCardDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return AIToolCard.objects.get(pk=pk)
        except AIToolCard.DoesNotExist:
            return None

    def get(self, request, pk):
        tool = self.get_object(pk)
        if not tool:
            return Response({"detail": "AI Tool card not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AIToolCardSerializer(tool, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        tool = self.get_object(pk)
        if not tool:
            return Response({"detail": "AI Tool card not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AIToolCardSerializer(tool, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        tool = self.get_object(pk)
        if not tool:
            return Response({"detail": "AI Tool card not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AIToolCardSerializer(tool, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk):
    #     if not (request.user and request.user.is_staff):
    #         return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
    #     tool = self.get_object(pk)
    #     if not tool:
    #         return Response({"detail": "AI Tool card not found."}, status=status.HTTP_404_NOT_FOUND)
    #     tool.delete()
    #     return Response({"message": "AI Tool card deleted successfully."}, status=status.HTTP_200_OK)

class LandingStatsBannerDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return LandingStatsBanner.objects.get(pk=pk)
        except LandingStatsBanner.DoesNotExist:
            return None

    def get(self, request, pk):
        stat = self.get_object(pk)
        if not stat:
            return Response({"detail": "Stats banner not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingStatsBannerSerializer(stat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        stat = self.get_object(pk)
        if not stat:
            return Response({"detail": "Stats banner not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingStatsBannerSerializer(stat, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        stat = self.get_object(pk)
        if not stat:
            return Response({"detail": "Stats banner not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = LandingStatsBannerSerializer(stat, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        stat = self.get_object(pk)
        if not stat:
            return Response({"detail": "Stats banner not found."}, status=status.HTTP_404_NOT_FOUND)
        stat.delete()
        return Response({"message": "Stats banner deleted successfully."}, status=status.HTTP_200_OK)



class AITutorSpotlightDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return AITutorSpotlight.objects.get(pk=pk)
        except AITutorSpotlight.DoesNotExist:
            return None

    def get(self, request, pk):
        spotlight = self.get_object(pk)
        if not spotlight:
            return Response({"detail": "AI Tutor Spotlight section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AITutorSpotlightSerializer(spotlight, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        spotlight = self.get_object(pk)
        if not spotlight:
            return Response({"detail": "AI Tutor Spotlight section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AITutorSpotlightSerializer(spotlight, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        spotlight = self.get_object(pk)
        if not spotlight:
            return Response({"detail": "AI Tutor Spotlight section not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AITutorSpotlightSerializer(spotlight, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not (request.user and request.user.is_staff):
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        spotlight = self.get_object(pk)
        if not spotlight:
            return Response({"detail": "AI Tutor Spotlight section not found."}, status=status.HTTP_404_NOT_FOUND)
        spotlight.delete()
        return Response({"message": "AI Tutor Spotlight section deleted successfully."}, status=status.HTTP_200_OK)