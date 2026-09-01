from django.shortcuts import render
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import NursingConceptMap
from .services import get_welcome_message, update_nursing_concept_map


def get_user_from_request(request):
    if request.user and request.user.is_authenticated:
        return request.user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_staff=True).first() or User.objects.first()


class ConceptMapVisualizerView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return render(request, "concept_map_visualizer.html")


class ConceptMapDetailView(APIView):
    """
    GET /api/concept-map/
    PUT /api/concept-map/
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response(
                {"error": "No valid user found in system."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        existing = NursingConceptMap.objects.filter(user=user, is_current=True).first()

        if not existing:
            # Fallback: get the most recently updated one and set it as current
            existing = NursingConceptMap.objects.filter(user=user).order_by("-updated_at").first()
            if existing:
                existing.is_current = True
                existing.save()

        if not existing:
            return Response(
                {
                    "exists": False,
                    "welcome_message": get_welcome_message(),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "exists": True,
                "map": existing.to_dict(),
                "updated_at": existing.updated_at,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        """
        PUT /api/concept-map/
        Body: {"title": "...", "nodes": [...], "edges": [...]}

        Directly saves manually edited nodes, category/color updates, or edges.
        """
        user = get_user_from_request(request)
        if not user:
            return Response(
                {"error": "No valid user found in system."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        nodes = request.data.get("nodes")
        edges = request.data.get("edges")
        if nodes is None or edges is None:
            return Response(
                {"error": "`nodes` and `edges` fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = NursingConceptMap.objects.filter(user=user, is_current=True).first()
        if not existing:
            existing = NursingConceptMap.objects.filter(user=user).order_by("-updated_at").first()
            if existing:
                existing.is_current = True
                existing.save()

        if not existing:
            existing = NursingConceptMap.objects.create(
                user=user,
                title=request.data.get("title", "Clinical Concept Map"),
                nodes=nodes,
                edges=edges,
                is_current=True,
            )
        else:
            existing.title = request.data.get("title", existing.title)
            existing.nodes = nodes
            existing.edges = edges
            existing.save()

        return Response(
            {
                "message": "Concept map updated successfully.",
                "exists": True,
                "map": existing.to_dict(),
                "updated_at": existing.updated_at,
            },
            status=status.HTTP_200_OK,
        )


class ConceptMapGenerateView(APIView):
    """
    POST /api/concept-map/generate/
    Accepts JSON body: {"prompt": "..."}
    OR Multipart Form Data: file: <File>, prompt: "..."
    """

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response(
                {"error": "No valid user found in system."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        prompt = (request.data.get("prompt") or "").strip()
        uploaded_file = request.FILES.get("file") or request.FILES.get("document")

        if not prompt and not uploaded_file:
            return Response(
                {"error": "Please provide a clinical text prompt or upload a file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = NursingConceptMap.objects.filter(user=user, is_current=True).first()
        if not existing:
            existing = NursingConceptMap.objects.filter(user=user).order_by("-updated_at").first()

        try:
            # Generate clean concept map based on user's latest prompt and/or uploaded file
            result = update_nursing_concept_map(
                user_prompt=prompt,
                current_concept_map=None,
                uploaded_file=uploaded_file,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"error": f"Failed to generate concept map: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # Overwrite user's current map or create a new current map
        if existing:
            existing.title = result.get("title", "Clinical Concept Map")
            existing.nodes = result.get("nodes", [])
            existing.edges = result.get("edges", [])
            existing.is_current = True
            existing.save()
        else:
            existing = NursingConceptMap.objects.create(
                user=user,
                title=result.get("title", "Clinical Concept Map"),
                nodes=result.get("nodes", []),
                edges=result.get("edges", []),
                is_current=True,
            )

        return Response(existing.to_dict(), status=status.HTTP_200_OK)


class ConceptMapListView(APIView):
    """
    GET /api/concept-maps/ -> List all maps for user
    POST /api/concept-maps/ -> Create a new empty map
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        maps = NursingConceptMap.objects.filter(user=user).order_by("-updated_at")
        data = []
        for m in maps:
            data.append({
                "id": m.id,
                "title": m.title,
                "nodes_count": len(m.nodes or []),
                "edges_count": len(m.edges or []),
                "updated_at": m.updated_at,
                "is_current": m.is_current,
                "subtitle": m.subtitle,
                "snippet": m.snippet
            })

        total_nodes = sum(len(m.nodes or []) for m in maps)
        return Response({
            "maps": data,
            "total_maps": len(data),
            "total_nodes": total_nodes
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        new_map = NursingConceptMap.objects.create(
            user=user,
            title=request.data.get("title", "Untitled Concept Map"),
            nodes=[],
            edges=[],
            is_current=True
        )
        return Response(new_map.to_dict(), status=status.HTTP_201_CREATED)


class ConceptMapSelectView(APIView):
    """
    POST /api/concept-maps/<pk>/select/ -> Make specific map active/current
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, pk):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            concept_map = NursingConceptMap.objects.get(pk=pk, user=user)
        except NursingConceptMap.DoesNotExist:
            return Response({"error": "Concept map not found."}, status=status.HTTP_404_NOT_FOUND)

        concept_map.is_current = True
        concept_map.save()

        return Response({
            "exists": True,
            "map": concept_map.to_dict(),
            "updated_at": concept_map.updated_at
        }, status=status.HTTP_200_OK)


class ConceptMapDeleteView(APIView):
    """
    DELETE /api/concept-maps/<pk>/ -> Delete specific map
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            concept_map = NursingConceptMap.objects.get(pk=pk, user=user)
        except NursingConceptMap.DoesNotExist:
            return Response({"error": "Concept map not found."}, status=status.HTTP_404_NOT_FOUND)

        was_current = concept_map.is_current
        concept_map.delete()

        if was_current:
            # Activate next most recently updated map
            next_map = NursingConceptMap.objects.filter(user=user).order_by("-updated_at").first()
            if next_map:
                next_map.is_current = True
                next_map.save()

        return Response({"message": "Concept map deleted successfully."}, status=status.HTTP_200_OK)


class ConceptMapClearView(APIView):
    """
    DELETE /api/concept-maps/clear/ -> Delete all concept maps of the user
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def delete(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        NursingConceptMap.objects.filter(user=user).delete()
        return Response({"message": "All concept maps cleared successfully."}, status=status.HTTP_200_OK)


class ConceptMapImportView(APIView):
    """
    POST /api/concept-maps/import/ -> Import map from JSON body
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response({"error": "No valid user found."}, status=status.HTTP_401_UNAUTHORIZED)

        title = request.data.get("title", "Imported Concept Map")
        nodes = request.data.get("nodes", [])
        edges = request.data.get("edges", [])

        new_map = NursingConceptMap.objects.create(
            user=user,
            title=title,
            nodes=nodes,
            edges=edges,
            is_current=True
        )

        return Response({
            "message": "Concept map imported successfully.",
            "map": new_map.to_dict()
        }, status=status.HTTP_201_CREATED)

