from typing import Protocol, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from app.db.models.qr import PrescriptionQR, PatientHistoryQR, HistoryAccessLog
from app.db.models.prescriptions import Prescription

class PrescriptionQRRepository(Protocol):
    async def create(self, qr: PrescriptionQR) -> PrescriptionQR:
        ...
        
    async def get_active_for_prescription(self, prescription_id: UUID) -> Optional[PrescriptionQR]:
        ...
        
    async def claim_qr(self, token: str, patient_id: UUID) -> Optional[UUID]:
        ...
        
    async def get_by_id(self, qr_id: UUID) -> Optional[PrescriptionQR]:
        ...

class SQLAlchemyPrescriptionQRRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, qr: PrescriptionQR) -> PrescriptionQR:
        self.session.add(qr)
        await self.session.commit()
        await self.session.refresh(qr)
        return qr

    async def get_active_for_prescription(self, prescription_id: UUID) -> Optional[PrescriptionQR]:
        result = await self.session.execute(
            select(PrescriptionQR)
            .where(PrescriptionQR.prescription_id == prescription_id)
            .where(PrescriptionQR.status == "active")
            .where(PrescriptionQR.expires_at > datetime.now(timezone.utc))
        )
        return result.scalar_one_or_none()

    async def claim_qr(self, token: str, patient_id: UUID) -> Optional[UUID]:
        # Atomic claim logic as per requirements
        stmt = (
            update(PrescriptionQR)
            .where(PrescriptionQR.token == token)
            .where(PrescriptionQR.status == "active")
            .where(PrescriptionQR.expires_at > datetime.now(timezone.utc))
            .values(
                status="claimed",
                claimed_by=patient_id,
                claimed_at=datetime.now(timezone.utc)
            )
            .returning(PrescriptionQR.prescription_id)
        )
        
        result = await self.session.execute(stmt)
        prescription_id = result.scalar_one_or_none()
        
        if prescription_id:
            # Also update the prescription's patient_id and status
            await self.session.execute(
                update(Prescription)
                .where(Prescription.id == prescription_id)
                .values(
                    patient_id=patient_id,
                    status="claimed"
                )
            )
            await self.session.commit()
            return prescription_id
            
        await self.session.commit()
        return None

    async def get_by_id(self, qr_id: UUID) -> Optional[PrescriptionQR]:
        result = await self.session.execute(
            select(PrescriptionQR).where(PrescriptionQR.id == qr_id)
        )
        return result.scalar_one_or_none()

class PatientHistoryQRRepository(Protocol):
    async def create(self, qr: PatientHistoryQR) -> PatientHistoryQR:
        ...
        
    async def get_active_by_token(self, token: str) -> Optional[PatientHistoryQR]:
        ...
        
    async def log_access(self, log: HistoryAccessLog) -> HistoryAccessLog:
        ...
        
    async def get_access_logs(self, patient_id: UUID) -> list[HistoryAccessLog]:
        ...

class SQLAlchemyPatientHistoryQRRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, qr: PatientHistoryQR) -> PatientHistoryQR:
        self.session.add(qr)
        await self.session.commit()
        await self.session.refresh(qr)
        return qr

    async def get_active_by_token(self, token: str) -> Optional[PatientHistoryQR]:
        result = await self.session.execute(
            select(PatientHistoryQR)
            .where(PatientHistoryQR.token == token)
            .where(PatientHistoryQR.status == "active")
            .where(PatientHistoryQR.expires_at > datetime.now(timezone.utc))
        )
        return result.scalar_one_or_none()

    async def log_access(self, log: HistoryAccessLog) -> HistoryAccessLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_access_logs(self, patient_id: UUID) -> list[HistoryAccessLog]:
        result = await self.session.execute(
            select(HistoryAccessLog)
            .join(PatientHistoryQR)
            .where(PatientHistoryQR.patient_id == patient_id)
            .order_by(HistoryAccessLog.accessed_at.desc())
        )
        return list(result.scalars().all())
