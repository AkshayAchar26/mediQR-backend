from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class OCRUploadResponse(BaseModel):
    id: UUID
    status: str
    original_image_url: str
    message: str

class OCRReviewResponse(BaseModel):
    id: UUID
    source_type: str
    uploaded_by: Optional[str]
    original_image_url: Optional[str]
    ai_extracted_json: Optional[Any]
    ai_confidence_score: Optional[float]
    review_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class OCREditRequest(BaseModel):
    ai_extracted_json: Any

class OCRConfirmRequest(BaseModel):
    # This is basically a PrescriptionCreateRequest but it could just take the 
    # modified ai_extracted_json from the frontend or rely on what's in the DB.
    # We will rely on what's in the DB to prevent client-side spoofing, 
    # so the doctor must PATCH it first if they want to edit, then POST to confirm.
    pass
