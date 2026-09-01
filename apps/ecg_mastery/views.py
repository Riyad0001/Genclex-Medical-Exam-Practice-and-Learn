from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import APIView, api_view
from rest_framework.response import Response
from .models import Diagnostic, Dosage, ECGPage
from .serializers import DiagnosticSerializer, ECGPageSerializer, DosageSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class ECGAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):

        if pk:
            try:
                page = ECGPage.objects.get(id=pk, user=request.user)

                serializer = ECGPageSerializer(
                    page,
                    context={'request': request})

                return Response({
                    "success": True,
                    "data": serializer.data})

            except ECGPage.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "ECG page not found"}, status=404)

        pages = ECGPage.objects.filter(user=request.user)

        serializer = ECGPageSerializer(
            pages,
            many=True,
            context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data})
    


class ECGSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        page_id = request.data.get("page_id")
        is_saved = request.data.get("is_saved")

        if page_id is None or is_saved is None:
            return Response({
                "success": False,
                "data": {
                    "message": "page_id and is_saved are required"
                }
            }, status=400)

        try:
            page = ECGPage.objects.get(id=page_id, user=request.user)
        except ECGPage.DoesNotExist:
            return Response({
                "success": False,
                "data": {
                    "message": "ECG page not found"
                }
            }, status=404)

        page.is_saved = is_saved
        page.save()

        serializer = ECGPageSerializer(page, context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data
        }, status=200)
    



# ----------------------------------------- Diagnostic Views -----------------------------------------#

class DiagnosticAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):

        if pk:
            try:
                page = Diagnostic.objects.get(id=pk, user=request.user)

                serializer = DiagnosticSerializer(
                    page,
                    context={'request': request})

                return Response({
                    "success": True,
                    "data": serializer.data})

            except Diagnostic.DoesNotExist:
                return Response({
                    "success": False,
                    "message": " Diagnostic not found"}, status=404)

        pages = Diagnostic.objects.filter(user=request.user)

        serializer = DiagnosticSerializer(
            pages,
            many=True,
            context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data})



class DiagnosticSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        page_id = request.data.get("page_id")
        is_saved = request.data.get("is_saved")

        if page_id is None or is_saved is None:
            return Response({
                "success": False,
                "data": {
                    "message": "diagnostic_id and is_saved are required"}}, status=400)

        if isinstance(is_saved, str):
            is_saved = is_saved.lower() == "true"

        try:
            page = Diagnostic.objects.get(id=page_id, user=request.user)
        except Diagnostic.DoesNotExist:
            return Response({
                "success": False,
                "data": {
                    "message": "Diagnostic not found"}}, status=404)

        page.is_saved = is_saved
        page.save()

        serializer = DiagnosticSerializer(page, context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data}, status=200)
    


# ----------------------------------------- Dosage Views -----------------------------------------#

class DosageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):

        if pk:
            try:
                page = Dosage.objects.get(id=pk, user=request.user)

                serializer = DosageSerializer(
                    page,
                    context={'request': request})

                return Response({
                    "success": True,
                    "data": serializer.data})

            except Dosage.DoesNotExist:
                return Response({
                    "success": False,
                    "message": " Dosage not found"}, status=404)

        pages = Dosage.objects.filter(user=request.user)

        serializer = DosageSerializer(
            pages,
            many=True,
            context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data})
    

class DosageSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        page_id = request.data.get("page_id")
        is_saved = request.data.get("is_saved")

        if page_id is None or is_saved is None:
            return Response({
                "success": False,
                "data": {
                    "message": "diagnostic_id and is_saved are required"}}, status=400)

        if isinstance(is_saved, str):
            is_saved = is_saved.lower() == "true"

        try:
            page = Dosage.objects.get(id=page_id, user=request.user)
        except Dosage.DoesNotExist:
            return Response({
                "success": False,
                "data": {
                    "message": "Dosage not found"}}, status=404)

        page.is_saved = is_saved
        page.save()

        serializer = DosageSerializer(page, context={'request': request})

        return Response({
            "success": True,
            "data": serializer.data}, status=200)
