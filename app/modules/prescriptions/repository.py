from typing import Protocol, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.prescriptions import Prescription, Medicine

class PrescriptionRepository(Protocol):
    async def create(self, prescription: Prescription) -> Prescription:
        ...
        
    async def get_by_id(self, prescription_id: UUID) -> Optional[Prescription]:
        ...
        
    async def list_by_doctor(self, doctor_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        ...
        
    async def list_by_patient(self, patient_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        ...

    async def get_by_ids(self, prescription_ids: List[UUID]) -> List[Prescription]:
        ...

class SQLAlchemyPrescriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, prescription: Prescription) -> Prescription:
        self.session.add(prescription)
        await self.session.commit()
        await self.session.refresh(prescription)
        
        # Load medicines to return full object
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.id == prescription.id)
        )
        return result.scalar_one()

    async def get_by_id(self, prescription_id: UUID) -> Optional[Prescription]:
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.id == prescription_id)
        )
        return result.scalar_one_or_none()

    async def list_by_doctor(self, doctor_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.doctor_id == doctor_id)
            .order_by(Prescription.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_patient(self, patient_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_ids(self, prescription_ids: List[UUID]) -> List[Prescription]:
        result = await self.session.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.id.in_(prescription_ids))
        )
        return list(result.scalars().all())
