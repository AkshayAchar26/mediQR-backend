from typing import Protocol, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.users import Patient

class PatientRepository(Protocol):
    async def create(self, patient: Patient) -> Patient:
        ...
        
    async def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        ...
        
    async def get_by_phone(self, phone: str) -> Optional[Patient]:
        ...
        
    async def get_by_email(self, email: str) -> Optional[Patient]:
        ...
        
    async def update(self, patient: Patient) -> Patient:
        ...

class SQLAlchemyPatientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        result = await self.session.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[Patient]:
        result = await self.session.execute(select(Patient).where(Patient.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Patient]:
        result = await self.session.execute(select(Patient).where(Patient.email == email))
        return result.scalar_one_or_none()

    async def update(self, patient: Patient) -> Patient:
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

