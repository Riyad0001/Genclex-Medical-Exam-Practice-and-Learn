
from rest_framework.decorators import APIView, api_view
from rest_framework.response import Response
from apps.procedure_lockup.models import ProcedureModule, Lecture_Notes
from .serializers import ProcedureSerializer, NoteSerializer, AIFormatSerializer, NoteSerializer, AIFormatSerializer
from .ai_formatter import AIFormatterService
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status


class ProcedureAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        # Single Get
        if pk is not None:
            module = get_object_or_404(ProcedureModule, pk=pk)
            serializer = ProcedureSerializer(
                module,
                context={"request": request}
            )
            return Response({"data": serializer.data})

        # List Get
        modules = ProcedureModule.objects.all().order_by("-id")
        serializer = ProcedureSerializer(
            modules,
            many=True,
            context={"request": request}
        )
        return Response({"data": serializer.data})



class AIFormatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIFormatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # title = serializer.validated_data["title"]
        html = serializer.validated_data["html"]

        formatted_html = AIFormatterService.format_html(html)

        note = Lecture_Notes.objects.create(
            user=request.user,
            # title=title,
            user_html=html,
            formatted_html=formatted_html,
        )

        return Response(
            {
                "id": note.id,
                "title": note.title,
                "formatted_html": note.formatted_html,
            },
            status=status.HTTP_201_CREATED,
        )
    


class NoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Create Note
    def post(self, request):
        serializer = NoteSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response(
                {
                    "success": True,
                    "message": "Note created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # List All Notes / Single Note
    def get(self, request, pk=None):

        if pk:
            note = get_object_or_404(Lecture_Notes, pk=pk, user=request.user)
            serializer = NoteSerializer(note, context={"request": request})

            return Response(
                {
                    "success": True,
                    "message": "Lecture note retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        notes = Lecture_Notes.objects.filter(user=request.user).order_by("-id")
        serializer = NoteSerializer(
            notes,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "success": True,
                "message": "Lecture notes retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # Update Note
    def put(self, request, pk):
        note = get_object_or_404(Lecture_Notes, pk=pk, user=request.user)

        serializer = NoteSerializer(
            note,
            data=request.data,
            partial=False,
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Note updated successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Delete Note
    def delete(self, request, pk):
        note = get_object_or_404(Lecture_Notes, pk=pk, user=request.user)
        note.delete()

        return Response(
            {
                "success": True,
                "message": "Note deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )

