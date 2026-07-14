from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.base import get_db_session
from app.core.deps import get_token_payload, require_doctor
from app.modules.ocr.schemas import OCRUploadResponse, OCRReviewResponse, OCREditRequest, OCRConfirmRequest
from app.modules.ocr.service import OCRService
from app.modules.ocr.repository import OCRRepository
from app.modules.prescriptions.service import PrescriptionService
from app.modules.prescriptions.repository import SQLAlchemyPrescriptionRepository
from app.modules.doctors.repository import SQLAlchemyDoctorRepository
from app.core.storage import get_storage_service
from app.core.ai import get_ai_service

router = APIRouter(prefix="/ocr", tags=["OCR"])

def get_ocr_service(db: AsyncSession = Depends(get_db_session)) -> OCRService:
    repository = OCRRepository(db)
    prescription_repo = SQLAlchemyPrescriptionRepository(db)
    doctor_repo = SQLAlchemyDoctorRepository(db)
    prescription_service = PrescriptionService(prescription_repo, doctor_repo)
    return OCRService(repository, prescription_service, get_storage_service(), get_ai_service())

@router.post("/upload", response_model=dict, status_code=201)
async def upload_prescription_image(
    file: UploadFile = File(...),
    payload: dict = Depends(get_token_payload),
    service: OCRService = Depends(get_ocr_service)
):
    """
    Upload an image for OCR extraction. Can be called by Doctor or Patient.
    """
    # Anyone logged in can upload, but only doctors can confirm.
    role = payload.get("role")
    
    source = await service.upload_and_extract(file, uploaded_by=role)
    response = OCRUploadResponse(
        id=source.id,
        status=source.review_status,
        original_image_url=source.original_image_url,
        message="Image uploaded and extraction completed."
    )
    return {"data": response.model_dump(mode='json'), "error": None}

@router.get("/{source_id}", response_model=dict)
async def get_ocr_extraction(
    source_id: UUID,
    payload: dict = Depends(get_token_payload),
    service: OCRService = Depends(get_ocr_service)
):
    """
    Get the extracted JSON and image URL for review.
    """
    source = await service.get_review_payload(source_id)
    return {"data": OCRReviewResponse.model_validate(source).model_dump(mode='json'), "error": None}

@router.patch("/{source_id}", response_model=dict)
async def edit_ocr_extraction(
    source_id: UUID,
    request: OCREditRequest,
    doctor_id: str = Depends(require_doctor),
    service: OCRService = Depends(get_ocr_service)
):
    """
    Edit the AI extracted JSON if there were mistakes.
    """
    source = await service.edit_extraction(source_id, request.ai_extracted_json)
    return {"data": OCRReviewResponse.model_validate(source).model_dump(mode='json'), "error": None}

@router.post("/{source_id}/confirm", response_model=dict)
async def confirm_ocr_extraction(
    source_id: UUID,
    doctor_id: str = Depends(require_doctor),
    service: OCRService = Depends(get_ocr_service)
):
    """
    Finalize the extraction and create the official Prescription in the database.
    """
    source = await service.confirm_extraction(source_id, UUID(doctor_id))
    return {"data": OCRReviewResponse.model_validate(source).model_dump(mode='json'), "error": None}
