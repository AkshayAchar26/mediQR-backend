from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.sources import PrescriptionSource
from uuid import UUID
from typing import Optional

class OCRRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, source: PrescriptionSource) -> PrescriptionSource:
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def get_by_id(self, source_id: UUID) -> Optional[PrescriptionSource]:
        result = await self.session.execute(
            select(PrescriptionSource).where(PrescriptionSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def update(self, source_id: UUID, **kwargs) -> Optional[PrescriptionSource]:
        result = await self.session.execute(
            update(PrescriptionSource)
            .where(PrescriptionSource.id == source_id)
            .values(**kwargs)
            .returning(PrescriptionSource)
        )
        await self.session.commit()
        return result.scalar_one_or_none()
