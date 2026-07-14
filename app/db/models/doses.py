import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.base import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .prescriptions import Medicine

class DoseLog(Base):
    __tablename__ = "dose_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    medicine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    scheduled_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    marked_status: Mapped[str | None] = mapped_column(String, nullable=True) # 'taken' or 'taken_late'
    marked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("medicine_id", "scheduled_datetime", name="uq_dose_logs_medicine_scheduled"),
    )

    # Relationships
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="dose_logs")
