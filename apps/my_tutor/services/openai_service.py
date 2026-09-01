import httpx
import logging
from django.conf import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    @staticmethod
    def get_async_client() -> AsyncOpenAI:
        """
        Get an initialized AsyncOpenAI client instance.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured in Django settings.")
        return AsyncOpenAI(api_key=api_key)

    @staticmethod
    async def generate_realtime_session(instructions: str = None) -> dict:
        """
        Generate an ephemeral WebRTC session key from OpenAI Realtime API.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured in Django settings.")

        url = "https://api.openai.com/v1/realtime/client_secrets"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Default session config wrapped in session object (GA syntax)
        payload = {
            "session": {
                "type": "realtime",
                "model": "gpt-realtime"
            }
        }
        
        if instructions:
            payload["session"]["instructions"] = instructions





        logger.info("Requesting OpenAI WebRTC session token...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                if response.status_code != 200:
                    logger.error(f"OpenAI sessions API returned status {response.status_code}: {response.text}")
                    raise ValueError(f"OpenAI error: {response.text}")
                
                return response.json()
            except Exception as e:
                logger.error(f"Exception calling OpenAI Realtime session API: {str(e)}")
                raise
