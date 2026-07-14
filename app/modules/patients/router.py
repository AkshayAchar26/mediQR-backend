from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.base import get_db_session
from app.core.deps import get_token_payload, require_patient
from app.core.exceptions import UnauthorizedError
from app.modules.patients.schemas import PatientRegisterRequest, PatientResponse, PatientUpdateRequest
from app.modules.patients.service import PatientService
from app.modules.patients.repository import SQLAlchemyPatientRepository

router = APIRouter(prefix="/patients", tags=["Patients"])

def get_patient_service(db: AsyncSession = Depends(get_db_session)) -> PatientService:
    repository = SQLAlchemyPatientRepository(db)
    return PatientService(repository=repository)

@router.post("/register", response_model=dict, status_code=201)
async def register_patient(
    request: PatientRegisterRequest,
    payload: dict = Depends(get_token_payload),
    service: PatientService = Depends(get_patient_service)
):
    """
    Registers a patient. Requires a temporary token obtained from OTP verification.
    """
    if payload.get("role") != "unregistered":
        raise UnauthorizedError("Must be unregistered to register.")
    
    email = payload.get("email")
    if not email:
        raise UnauthorizedError("Token does not contain an email address.")
        
    patient = await service.register_patient(email=email, data=request)
    return {"data": PatientResponse.model_validate(patient).model_dump(mode='json'), "error": None}

@router.get("/me", response_model=dict)
async def get_my_profile(
    patient_id: str = Depends(require_patient),
    service: PatientService = Depends(get_patient_service)
):
    patient = await service.get_patient_profile(UUID(patient_id))
    return {"data": PatientResponse.model_validate(patient).model_dump(mode='json'), "error": None}

@router.patch("/me", response_model=dict)
async def update_my_profile(
    request: PatientUpdateRequest,
    patient_id: str = Depends(require_patient),
    service: PatientService = Depends(get_patient_service)
):
    patient = await service.update_patient_profile(UUID(patient_id), request)
    return {"data": PatientResponse.model_validate(patient).model_dump(mode='json'), "error": None}
