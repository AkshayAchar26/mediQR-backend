from app.modules.patients.repository import PatientRepository
from app.modules.patients.schemas import PatientRegisterRequest, PatientUpdateRequest
from app.db.models.users import Patient
from app.core.exceptions import ConflictError, NotFoundError
from uuid import UUID

class PatientService:
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    async def register_patient(self, email: str, data: PatientRegisterRequest) -> Patient:
        existing_email = await self.repository.get_by_email(email)
        if existing_email:
            raise ConflictError("A patient with this email is already registered.")

        existing_phone = await self.repository.get_by_phone(data.phone)
        if existing_phone:
            raise ConflictError("A patient with this phone number is already registered.")

        patient = Patient(
            name=data.name,
            email=email,
            phone=data.phone,
            dob=data.dob
        )
        return await self.repository.create(patient)

    async def get_patient_profile(self, patient_id: UUID) -> Patient:
        patient = await self.repository.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient profile not found.")
        return patient

    async def update_patient_profile(self, patient_id: UUID, data: PatientUpdateRequest) -> Patient:
        patient = await self.repository.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient profile not found.")
        
        if data.name is not None:
            patient.name = data.name
        if data.dob is not None:
            patient.dob = data.dob
            
        return await self.repository.update(patient)
