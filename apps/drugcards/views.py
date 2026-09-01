"""
views.py
========

Thin Django view layer. Contains ONLY view functions — all drug-card
generation logic lives in drug_card_generator.py and is simply imported
and called here.

This is a direct, line-for-line conversion of the original Flask
app.py routes to Django views. Behavior is unchanged:

    GET  /                  -> index
    GET  /api/quick-picks   -> api_quick_picks
    POST /api/generate      -> api_generate
    POST /api/cache/clear   -> api_clear_cache
    GET  /api/health        -> api_health

History endpoints (require authentication):
    GET    /api/history/          -> list all drug card history for the user
    GET    /api/history/<pk>/     -> retrieve a single saved drug card (full card_data)
    DELETE /api/history/<pk>/     -> delete a single saved drug card
    DELETE /api/history/          -> delete ALL history for the user
"""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import drug_card_generator as dcg
from .models import DrugCardHistory
from .serializers import DrugCardHistoryListSerializer, DrugCardHistorySerializer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drug-card-app")


# ---------------------------------------------------------------------------
# Original views (unchanged)
# ---------------------------------------------------------------------------

@require_GET
def index(request):
    return render(request, "drugcards/index.html", {"quick_picks": dcg.QUICK_PICK_DRUGS})


@require_GET
def api_quick_picks(request):
    return JsonResponse({"drugs": dcg.QUICK_PICK_DRUGS})


class DrugCardGenerateView(APIView):
    """POST /api/drugcards/generate/ -> generate a drug card and save to history"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = request.data or {}
        except Exception:
            payload = {}

        drug_name = payload.get("drug_name", "")
        force_refresh = bool(payload.get("force_refresh", False))

        logger.info("api_generate request for drug_name=%r, force_refresh=%r", drug_name, force_refresh)

        try:
            card = dcg.get_drug_card(drug_name, use_cache=not force_refresh)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.exception("Unexpected error generating drug card")
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save to history if user is authenticated
        history_id = None
        if request.user and request.user.is_authenticated:
            record = DrugCardHistory.objects.create(
                user=request.user,
                drug_name=card.get("drug_name", drug_name),
                card_data=card,
            )
            history_id = record.id

        return Response({"card": card, "history_id": history_id})


@csrf_exempt
@require_POST
def api_clear_cache(request):
    dcg.clear_cache()
    return JsonResponse({"status": "cache cleared"})


@require_GET
def api_health(request):
    return JsonResponse({
        "status": "ok",
        "model": dcg.OPENAI_MODEL,
        "api_key_configured": bool(dcg.OPENAI_API_KEY),
    })


# ---------------------------------------------------------------------------
# History views (require authentication)
# ---------------------------------------------------------------------------

class DrugCardHistoryListView(APIView):
    """
    GET    /api/drugcards/history/  -> list all drug cards for the logged-in user
    DELETE /api/drugcards/history/  -> delete ALL history for the logged-in user
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = DrugCardHistory.objects.filter(user=request.user)
        serializer = DrugCardHistoryListSerializer(records, many=True)
        return Response({
            "data": serializer.data,
            "meta": {"total": records.count()},
        })

    def delete(self, request):
        deleted_count, _ = DrugCardHistory.objects.filter(user=request.user).delete()
        return Response({
            "data": {"deleted": deleted_count},
            "meta": {"operation": "clear_history"},
        })


class DrugCardHistoryDetailView(APIView):
    """
    GET    /api/drugcards/history/<pk>/  -> retrieve a single saved drug card (full card_data)
    DELETE /api/drugcards/history/<pk>/  -> delete a single saved drug card
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_record(self, pk, user):
        try:
            return DrugCardHistory.objects.get(pk=pk, user=user), None
        except DrugCardHistory.DoesNotExist:
            return None, Response(
                {"detail": "Drug card not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, pk):
        record, error = self._get_record(pk, request.user)
        if error:
            return error
        serializer = DrugCardHistorySerializer(record)
        return Response({"data": serializer.data})

    def delete(self, request, pk):
        record, error = self._get_record(pk, request.user)
        if error:
            return error
        record.delete()
        return Response({
            "data": {"deleted": pk},
            "meta": {"operation": "delete_history_item"},
        })
