from django.shortcuts import render
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import services
from .models import CarePlanHistory
from .serializers import (
    CarePlanHistoryListSerializer,
    CarePlanHistorySerializer,
    EditRequestSerializer,
    GenerateRequestSerializer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(operation):
    """
    Mirrors backend_api.py's `run()` helper: executes `operation` and, if it
    raises, converts that into the same generic 502 error the FastAPI
    version returned (HTTPException(502, "Care-plan generation failed."))
    instead of leaking a raw traceback to the client.

    Returns a (result, error_response) tuple - exactly one of the two is
    non-None.
    """
    try:
        return operation(), None
    except Exception:
        return None, Response(
            {"detail": "Care-plan generation failed."},
            status=status.HTTP_502_BAD_GATEWAY,
        )


def _get_authenticated_user(request):
    """
    Returns the authenticated user from the request, or None.
    Supports JWT and Session authentication.
    """
    if request.user and request.user.is_authenticated:
        return request.user
    return None


def _extract_title(care_plan: dict) -> str:
    """Pull a human-readable title from the generated care plan."""
    metadata = care_plan.get("metadata", {})
    subtitle = metadata.get("subtitle", "")
    if subtitle:
        return subtitle[:255]
    return metadata.get("title", "Care Plan")[:255]


# ---------------------------------------------------------------------------
# Core generation / edit views (unchanged behaviour, now saves history)
# ---------------------------------------------------------------------------

class HealthView(APIView):
    """GET /api/health  ->  same payload as backend_api.py's health()"""

    def get(self, request):
        return Response({"data": {"status": "ok"}, "meta": {"api_version": "v1"}})


class CarePlanCreateView(APIView):
    """POST /api/care-plans  ->  generate a brand-new care plan and save to history"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        care_plan, error = _run(
            lambda: services.generate_care_plan(serializer.validated_data["patient"])
        )
        if error:
            return error

        # Save to history if user is authenticated
        user = _get_authenticated_user(request)
        history_id = None
        if user:
            record = CarePlanHistory.objects.create(
                user=user,
                title=_extract_title(care_plan),
                care_plan=care_plan,
            )
            history_id = record.id

        return Response({
            "data": {"care_plan": care_plan},
            "meta": {"operation": "generated", "history_id": history_id},
        })


class CarePlanEditView(APIView):
    """POST /api/care-plans/edit  ->  edit an existing care plan and save to history"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EditRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        care_plan, error = _run(
            lambda: services.edit_care_plan(validated["instruction"], validated["care_plan"])
        )
        if error:
            return error

        # Save to history if user is authenticated
        user = _get_authenticated_user(request)
        history_id = None
        if user:
            record = CarePlanHistory.objects.create(
                user=user,
                title=_extract_title(care_plan),
                care_plan=care_plan,
            )
            history_id = record.id

        return Response({
            "data": {"care_plan": care_plan},
            "meta": {"operation": "edited", "history_id": history_id},
        })


class AffectedSectionsView(APIView):
    """POST /api/care-plans/affected-sections  ->  routing preview"""

    def post(self, request):
        serializer = EditRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        affected, error = _run(
            lambda: services.identify_affected_sections(
                validated["instruction"], validated["care_plan"]
            )
        )
        if error:
            return error

        return Response(
            {"data": {"affected_sections": affected}, "meta": {"operation": "routed"}}
        )


# ---------------------------------------------------------------------------
# History views  (require authentication)
# ---------------------------------------------------------------------------

class CarePlanHistoryListView(APIView):
    """
    GET  /api/care-plans/history/   -> list all care plans for the logged-in user
    DELETE /api/care-plans/history/ -> delete ALL history for the logged-in user
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = CarePlanHistory.objects.filter(user=request.user)
        serializer = CarePlanHistoryListSerializer(records, many=True)
        return Response({
            "data": serializer.data,
            "meta": {"total": records.count()},
        })

    def delete(self, request):
        deleted_count, _ = CarePlanHistory.objects.filter(user=request.user).delete()
        return Response({
            "data": {"deleted": deleted_count},
            "meta": {"operation": "clear_history"},
        })


class CarePlanHistoryDetailView(APIView):
    """
    GET    /api/care-plans/history/<pk>/  -> retrieve a single saved care plan
    DELETE /api/care-plans/history/<pk>/  -> delete a single saved care plan
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_record(self, pk, user):
        try:
            return CarePlanHistory.objects.get(pk=pk, user=user), None
        except CarePlanHistory.DoesNotExist:
            return None, Response(
                {"detail": "Care plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request, pk):
        record, error = self._get_record(pk, request.user)
        if error:
            return error
        serializer = CarePlanHistorySerializer(record)
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


# ---------------------------------------------------------------------------
# Test page (HTML, not JSON)
# ---------------------------------------------------------------------------

def care_plan_test_page(request):
    """
    GET /test  ->  serves the standalone HTML UI, same as backend_api.py's
    FileResponse(Careplan.html). Plain Django view (not DRF) since it just
    renders a template, not JSON.
    """
    return render(request, "careplans/careplan.html")

class CarePlanTestView(APIView):
    """
    GET /api/care-plans/test/  ->  serves the standalone HTML UI (same as the old /test)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, "careplans/careplan.html")

class CarePlanShareView(APIView):
    """
    GET /api/care-plans/share/<pk>/  ->  share a care plan (returns JSON)
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        record, error = CarePlanHistoryDetailView()._get_record(pk, request.user)
        if error:
            return error
        return Response({
            "data": {
                "care_plan": record.care_plan,
                "share_url": f"https://your-domain.com/share/{pk}",
            },
            "meta": {"operation": "share"},
        })