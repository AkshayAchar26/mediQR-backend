import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from app.db.base import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .prescriptions import Prescription

class PrescriptionSource(Base):
    __tablename__ = "prescription_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    prescription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prescriptions.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False) # qr_generated, ocr_upload
    uploaded_by: Mapped[str | None] = mapped_column(String, nullable=True) # doctor, patient
    original_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_extracted_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    review_status: Mapped[str] = mapped_column(String, nullable=False, server_default="pending") # pending, confirmed, edited, rejected
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    prescription: Mapped[Optional["Prescription"]] = relationship("Prescription", back_populates="sources")
