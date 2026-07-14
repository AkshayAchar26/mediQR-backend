import structlog
import httpx
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.modules.prescriptions.schemas import PrescriptionCreateRequest

logger = structlog.get_logger(__name__)
settings = get_settings()

class AIService:
    def __init__(self):
        # We only initialize the client if the key is present
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None
        
    async def extract_prescription(self, image_url: str) -> dict:
        """
        Downloads the image from the given URL and sends it to Gemini to extract structured prescription data.
        Returns the data as a dictionary matching PrescriptionCreateRequest.
        """
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured.")
            
        logger.info("downloading_image_for_ai", url=image_url)
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download image for AI extraction. Status: {response.status_code}")
            image_bytes = response.content
            mime_type = response.headers.get("content-type", "image/jpeg")
            
        logger.info("calling_gemini_vision_api")
        
        prompt = """
        You are a medical assistant OCR tool. Your job is to extract prescription data from the provided image.
        Return the data strictly conforming to the provided JSON schema.
        - For 'till_date', if not explicitly mentioned, estimate based on the longest medicine course, or default to 30 days from today (format: YYYY-MM-DD).
        - For 'times_per_day', parse instructions like "morning and night" to ["08:00:00", "20:00:00"]. Use common sense 24-hour time formats.
        - If 'dosage' is missing, put 'As directed'.
        """
        
        # We must use synchronous call because google-genai's async client is client.aio
        # We will use client.aio.models.generate_content
        result = await self.client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PrescriptionCreateRequest,
                temperature=0.0
            ),
        )
        
        logger.info("gemini_vision_api_success")
        # result.text contains the JSON string
        import json
        return json.loads(result.text)

def get_ai_service() -> AIService:
    return AIService()
