import httpx
import structlog
import uuid
import mimetypes
from fastapi import UploadFile
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class StorageService:
    def __init__(self):
        self.base_url = f"{settings.supabase_url}/storage/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "apikey": settings.supabase_secret_key
        }

    async def upload_prescription_image(self, file: UploadFile) -> str:
        """
        Uploads a file to the 'prescriptions' public bucket in Supabase.
        Returns the public URL of the uploaded image.
        """
        # Read file contents
        content = await file.read()
        
        # Generate a unique filename
        ext = mimetypes.guess_extension(file.content_type or "") or ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        
        url = f"{self.base_url}/object/prescriptions/{filename}"
        
        headers = self.headers.copy()
        headers["Content-Type"] = file.content_type or "image/jpeg"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, content=content, headers=headers)
            
            if response.status_code not in (200, 201):
                logger.error("supabase_storage_upload_failed", status=response.status_code, body=response.text)
                raise Exception(f"Failed to upload image: {response.text}")
                
        # Return the public URL
        public_url = f"{self.base_url}/object/public/prescriptions/{filename}"
        return public_url

def get_storage_service() -> StorageService:
    return StorageService()
