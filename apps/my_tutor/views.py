from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
import logging
from .services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

from .consumers import SYSTEM_PROMPT

class VoiceSessionView(APIView):
    """
    Endpoint to request an ephemeral session token for OpenAI Realtime WebRTC.
    """
    def post(self, request, *args, **kwargs):
        system_instructions = SYSTEM_PROMPT
        try:
            # Execute async session creation synchronously
            session_data = async_to_sync(OpenAIService.generate_realtime_session)(system_instructions)
            return Response(session_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error creating voice session: {str(e)}")
            return Response(
                {"error": f"Failed to initialize voice session: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
