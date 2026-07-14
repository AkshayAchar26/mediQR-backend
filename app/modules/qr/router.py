from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.base import get_db_session
from app.core.deps import require_doctor, require_patient
from app.modules.qr.schemas import QRClaimRequest, QRResponse, QRClaimResponse, HistoryQRGenerateRequest, HistoryQRClaimRequest, PatientHistoryQRResponse, HistoryQRClaimResponse, HistoryAccessLogResponse
from app.modules.qr.service import QRService
from app.modules.qr.repository import SQLAlchemyPrescriptionQRRepository, SQLAlchemyPatientHistoryQRRepository
from app.modules.prescriptions.repository import SQLAlchemyPrescriptionRepository
from app.modules.prescriptions.service import PrescriptionService
from app.modules.doctors.repository import SQLAlchemyDoctorRepository

router = APIRouter(prefix="/qr", tags=["QR Codes"])

def get_qr_service(db: AsyncSession = Depends(get_db_session)) -> QRService:
    repository = SQLAlchemyPrescriptionQRRepository(db)
    prescription_repo = SQLAlchemyPrescriptionRepository(db)
    history_repo = SQLAlchemyPatientHistoryQRRepository(db)
    doctor_repo = SQLAlchemyDoctorRepository(db)
    prescription_service = PrescriptionService(prescription_repo, doctor_repo)
    return QRService(repository=repository, prescription_repo=prescription_repo, history_repository=history_repo, prescription_service=prescription_service)

@router.post("/prescription/claim", response_model=dict)
async def claim_prescription(
    request: QRClaimRequest,
    patient_id: str = Depends(require_patient),
    service: QRService = Depends(get_qr_service)
):
    """Claim a prescription using a QR token (Patient only)."""
    prescription_id = await service.claim_prescription_qr(UUID(patient_id), request.token)
    return {"data": QRClaimResponse(prescription_id=prescription_id).model_dump(mode='json'), "error": None}

@router.post("/prescription/{prescription_id}", response_model=dict, status_code=201)
async def generate_prescription_qr(
    prescription_id: UUID,
    doctor_id: str = Depends(require_doctor),
    service: QRService = Depends(get_qr_service)
):
    """Generate a one-time QR token for a prescription (Doctor only)."""
    qr = await service.generate_prescription_qr(UUID(doctor_id), prescription_id)
    return {"data": QRResponse.model_validate(qr).model_dump(mode='json'), "error": None}

@router.post("/history", response_model=dict, status_code=201)
async def generate_history_qr(
    request: HistoryQRGenerateRequest,
    patient_id: str = Depends(require_patient),
    service: QRService = Depends(get_qr_service)
):
    """Generate a history sharing QR token (Patient only)."""
    qr = await service.generate_history_qr(UUID(patient_id), request.scope, request.scope_prescription_ids)
    return {"data": PatientHistoryQRResponse.model_validate(qr).model_dump(mode='json'), "error": None}

@router.post("/history/claim", response_model=dict)
async def claim_history_qr(
    request: HistoryQRClaimRequest,
    doctor_id: str = Depends(require_doctor),
    service: QRService = Depends(get_qr_service)
):
    """Scan a patient's history QR token and retrieve their prescriptions (Doctor only)."""
    patient_id, prescriptions = await service.claim_history_qr(UUID(doctor_id), request.token)
    
    # We must construct a dictionary of the response
    from app.modules.prescriptions.schemas import PrescriptionListResponse
    return {
        "data": {
            "patient_id": str(patient_id),
            "prescriptions": [PrescriptionListResponse.model_validate(p).model_dump(mode='json') for p in prescriptions]
        },
        "error": None
    }

@router.get("/history/access-logs", response_model=dict)
async def get_access_logs(
    patient_id: str = Depends(require_patient),
    service: QRService = Depends(get_qr_service)
):
    """View access logs for history QR tokens (Patient only)."""
    logs = await service.get_access_logs(UUID(patient_id))
    return {"data": [HistoryAccessLogResponse.model_validate(log).model_dump(mode='json') for log in logs], "error": None}
