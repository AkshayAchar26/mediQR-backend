from app.modules.doctors.repository import DoctorRepository
from app.modules.doctors.schemas import DoctorRegisterRequest, DoctorUpdateRequest
from app.db.models.users import Doctor
from app.core.exceptions import ConflictError, NotFoundError
from uuid import UUID

class DoctorService:
    def __init__(self, repository: DoctorRepository):
        self.repository = repository

    async def register_doctor(self, email: str, data: DoctorRegisterRequest) -> Doctor:
        # Check if already exists by email
        existing_email = await self.repository.get_by_email(email)
        if existing_email:
            raise ConflictError("A doctor with this email is already registered.")

        # Check if already exists by phone
        existing_phone = await self.repository.get_by_phone(data.phone)
        if existing_phone:
            raise ConflictError("A doctor with this phone number is already registered.")

        # Create new
        doctor = Doctor(
            name=data.name,
            email=email,
            phone=data.phone,
            hospital_or_clinic=data.hospital_or_clinic,
            expertise=data.expertise
        )
        return await self.repository.create(doctor)

    async def get_doctor_profile(self, doctor_id: UUID) -> Doctor:
        doctor = await self.repository.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundError("Doctor profile not found.")
        return doctor

    async def update_doctor_profile(self, doctor_id: UUID, data: DoctorUpdateRequest) -> Doctor:
        doctor = await self.repository.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundError("Doctor profile not found.")
        
        if data.name is not None:
            doctor.name = data.name
        if data.hospital_or_clinic is not None:
            doctor.hospital_or_clinic = data.hospital_or_clinic
        if data.expertise is not None:
            doctor.expertise = data.expertise
            
        return await self.repository.update(doctor)
