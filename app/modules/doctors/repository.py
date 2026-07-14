from typing import Protocol, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.users import Doctor

class DoctorRepository(Protocol):
    async def create(self, doctor: Doctor) -> Doctor:
        ...
        
    async def get_by_id(self, doctor_id: UUID) -> Optional[Doctor]:
        ...
        
    async def get_by_phone(self, phone: str) -> Optional[Doctor]:
        ...
        
    async def get_by_email(self, email: str) -> Optional[Doctor]:
        ...
        
    async def update(self, doctor: Doctor) -> Doctor:
        ...

class SQLAlchemyDoctorRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, doctor: Doctor) -> Doctor:
        self.session.add(doctor)
        await self.session.commit()
        await self.session.refresh(doctor)
        return doctor

    async def get_by_id(self, doctor_id: UUID) -> Optional[Doctor]:
        result = await self.session.execute(select(Doctor).where(Doctor.id == doctor_id))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[Doctor]:
        result = await self.session.execute(select(Doctor).where(Doctor.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Doctor]:
        result = await self.session.execute(select(Doctor).where(Doctor.email == email))
        return result.scalar_one_or_none()

    async def update(self, doctor: Doctor) -> Doctor:
        await self.session.commit()
        await self.session.refresh(doctor)
        return doctor

