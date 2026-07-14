from typing import Protocol, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from app.db.models.doses import DoseLog

class DoseLogRepository(Protocol):
    async def get_by_id(self, dose_log_id: UUID) -> Optional[DoseLog]:
        ...
        
    async def list_for_prescription(self, prescription_id: UUID) -> List[DoseLog]:
        ...
        
    async def mark_taken(self, dose_log_id: UUID, status: str, marked_at: datetime) -> Optional[DoseLog]:
        ...

class SQLAlchemyDoseLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, dose_log_id: UUID) -> Optional[DoseLog]:
        result = await self.session.execute(
            select(DoseLog).where(DoseLog.id == dose_log_id)
        )
        return result.scalar_one_or_none()

    async def list_for_prescription(self, prescription_id: UUID) -> List[DoseLog]:
        # Need to join with Medicine to filter by prescription_id
        from app.db.models.prescriptions import Medicine
        result = await self.session.execute(
            select(DoseLog)
            .join(Medicine)
            .where(Medicine.prescription_id == prescription_id)
            .order_by(DoseLog.scheduled_datetime.asc())
        )
        return list(result.scalars().all())

    async def mark_taken(self, dose_log_id: UUID, status: str, marked_at: datetime) -> Optional[DoseLog]:
        # Write-once atomic update: only update if marked_status is NULL
        stmt = (
            update(DoseLog)
            .where(DoseLog.id == dose_log_id)
            .where(DoseLog.marked_status.is_(None))
            .values(
                marked_status=status,
                marked_at=marked_at
            )
            .returning(DoseLog)
        )
        
        result = await self.session.execute(stmt)
        dose_log = result.scalar_one_or_none()
        await self.session.commit()
        return dose_log
