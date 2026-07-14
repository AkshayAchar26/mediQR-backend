from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.db.base import get_db_session
from app.core.deps import get_token_payload, require_doctor, require_patient
from app.modules.prescriptions.schemas import PrescriptionCreateRequest, PrescriptionResponse, PrescriptionListResponse
from app.modules.prescriptions.service import PrescriptionService
from app.modules.prescriptions.repository import SQLAlchemyPrescriptionRepository
from app.modules.doctors.repository import SQLAlchemyDoctorRepository

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

def get_prescription_service(db: AsyncSession = Depends(get_db_session)) -> PrescriptionService:
    repository = SQLAlchemyPrescriptionRepository(db)
    doctor_repository = SQLAlchemyDoctorRepository(db)
    return PrescriptionService(repository=repository, doctor_repository=doctor_repository)

@router.post("", response_model=dict, status_code=201)
async def create_prescription(
    request: PrescriptionCreateRequest,
    doctor_id: str = Depends(require_doctor),
    service: PrescriptionService = Depends(get_prescription_service)
):
    prescription = await service.create_prescription(UUID(doctor_id), request)
    return {"data": PrescriptionResponse.model_validate(prescription).model_dump(mode='json'), "error": None}

@router.get("/mine", response_model=dict)
async def list_doctor_prescriptions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    doctor_id: str = Depends(require_doctor),
    service: PrescriptionService = Depends(get_prescription_service)
):
    prescriptions = await service.list_doctor_prescriptions(UUID(doctor_id), limit, offset)
    data = [PrescriptionListResponse.model_validate(p).model_dump(mode='json') for p in prescriptions]
    return {"data": data, "error": None}

@router.get("", response_model=dict)
async def list_patient_prescriptions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient_id: str = Depends(require_patient),
    service: PrescriptionService = Depends(get_prescription_service)
):
    prescriptions = await service.list_patient_prescriptions(UUID(patient_id), limit, offset)
    data = [PrescriptionListResponse.model_validate(p).model_dump(mode='json') for p in prescriptions]
    return {"data": data, "error": None}

@router.get("/{id}", response_model=dict)
async def get_prescription(
    id: UUID,
    payload: dict = Depends(get_token_payload),
    service: PrescriptionService = Depends(get_prescription_service)
):
    user_id = UUID(payload["sub"])
    role = payload["role"]
    prescription = await service.get_prescription(id, user_id, role)
    return {"data": PrescriptionResponse.model_validate(prescription).model_dump(mode='json'), "error": None}
