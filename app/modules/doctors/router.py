from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.base import get_db_session
from app.core.deps import get_token_payload, require_doctor, get_current_user_id
from app.core.exceptions import UnauthorizedError
from app.modules.doctors.schemas import DoctorRegisterRequest, DoctorResponse, DoctorUpdateRequest
from app.modules.doctors.service import DoctorService
from app.modules.doctors.repository import SQLAlchemyDoctorRepository

router = APIRouter(prefix="/doctors", tags=["Doctors"])

def get_doctor_service(db: AsyncSession = Depends(get_db_session)) -> DoctorService:
    repository = SQLAlchemyDoctorRepository(db)
    return DoctorService(repository=repository)

@router.post("/register", response_model=dict, status_code=201)
async def register_doctor(
    request: DoctorRegisterRequest,
    payload: dict = Depends(get_token_payload),
    service: DoctorService = Depends(get_doctor_service)
):
    """
    Registers a doctor. Requires a temporary token obtained from OTP verification.
    """
    if payload.get("role") != "unregistered":
        raise UnauthorizedError("Must be unregistered to register.")
    
    email = payload.get("email")
    if not email:
        raise UnauthorizedError("Token does not contain an email address.")
        
    doctor = await service.register_doctor(email=email, data=request)
    return {"data": DoctorResponse.model_validate(doctor).model_dump(mode='json'), "error": None}

@router.get("/me", response_model=dict)
async def get_my_profile(
    doctor_id: str = Depends(require_doctor),
    service: DoctorService = Depends(get_doctor_service)
):
    doctor = await service.get_doctor_profile(UUID(doctor_id))
    return {"data": DoctorResponse.model_validate(doctor).model_dump(mode='json'), "error": None}

@router.patch("/me", response_model=dict)
async def update_my_profile(
    request: DoctorUpdateRequest,
    doctor_id: str = Depends(require_doctor),
    service: DoctorService = Depends(get_doctor_service)
):
    doctor = await service.update_doctor_profile(UUID(doctor_id), request)
    return {"data": DoctorResponse.model_validate(doctor).model_dump(mode='json'), "error": None}
