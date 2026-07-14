from fastapi import UploadFile
from uuid import UUID
from app.modules.ocr.repository import OCRRepository
from app.modules.prescriptions.service import PrescriptionService
from app.modules.prescriptions.schemas import PrescriptionCreateRequest
from app.db.models.sources import PrescriptionSource
from app.core.exceptions import NotFoundError, AppError
from app.core.storage import StorageService
from app.core.ai import AIService
import structlog

logger = structlog.get_logger(__name__)

class OCRService:
    def __init__(self, repository: OCRRepository, prescription_service: PrescriptionService, storage_service: StorageService, ai_service: AIService):
        self.repository = repository
        self.prescription_service = prescription_service
        self.storage_service = storage_service
        self.ai_service = ai_service

    async def upload_and_extract(self, file: UploadFile, uploaded_by: str) -> PrescriptionSource:
        """
        Uploads image to Supabase, calls Gemini for extraction, and saves a draft.
        """
        if not file.content_type.startswith("image/"):
            raise AppError("INVALID_FILE", "File must be an image.")

        # 1. Upload to Supabase Storage
        image_url = await self.storage_service.upload_prescription_image(file)
        
        # 2. Save initial source record
        source = PrescriptionSource(
            source_type="ocr_upload",
            uploaded_by=uploaded_by,
            original_image_url=image_url,
            review_status="pending"
        )
        source = await self.repository.create(source)
        
        # 3. Call AI Extraction (Synchronously waiting for it, could be backgrounded)
        try:
            extracted_json = await self.ai_service.extract_prescription(image_url)
            # Update source with extracted JSON
            source = await self.repository.update(
                source.id,
                ai_extracted_json=extracted_json,
                # Confidence score could be added later or returned by AI
                ai_confidence_score=0.9
            )
        except Exception as e:
            logger.error("ai_extraction_failed", error=str(e), source_id=str(source.id))
            # Mark it as pending still, but maybe store error in JSON or status
            source = await self.repository.update(source.id, review_status="rejected")
            raise AppError("AI_EXTRACTION_FAILED", f"Failed to extract data: {str(e)}")
            
        return source

    async def get_review_payload(self, source_id: UUID) -> PrescriptionSource:
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise NotFoundError("OCR source not found.")
        return source

    async def edit_extraction(self, source_id: UUID, ai_extracted_json: dict) -> PrescriptionSource:
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise NotFoundError("OCR source not found.")
        if source.review_status == "confirmed":
            raise AppError("ALREADY_CONFIRMED", "Cannot edit a confirmed OCR extraction.")
            
        return await self.repository.update(
            source_id,
            ai_extracted_json=ai_extracted_json,
            review_status="edited"
        )

    async def confirm_extraction(self, source_id: UUID, doctor_id: UUID) -> PrescriptionSource:
        source = await self.repository.get_by_id(source_id)
        if not source:
            raise NotFoundError("OCR source not found.")
        if source.review_status == "confirmed":
            raise AppError("ALREADY_CONFIRMED", "This extraction is already confirmed.")
        if not source.ai_extracted_json:
            raise AppError("MISSING_DATA", "No data to confirm. Please edit first.")

        # Parse the JSON into PrescriptionCreateRequest
        try:
            request_data = PrescriptionCreateRequest(**source.ai_extracted_json)
        except Exception as e:
            raise AppError("INVALID_DATA", f"Data does not conform to schema: {str(e)}")

        # Create actual prescription
        prescription = await self.prescription_service.create_prescription(doctor_id, request_data)

        # Update source
        return await self.repository.update(
            source_id,
            prescription_id=prescription.id,
            review_status="confirmed"
        )
