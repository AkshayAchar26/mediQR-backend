import uuid
from datetime import datetime, date, time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Date, ForeignKey, ARRAY, TIME
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.base import Base
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .users import Doctor, Patient
    from .doses import DoseLog
    from .qr import PrescriptionQR
    from .sources import PrescriptionSource

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    hospital_or_clinic: Mapped[str] = mapped_column(String, nullable=False)
    till_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="unclaimed")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="prescriptions")
    patient: Mapped[Optional["Patient"]] = relationship("Patient", back_populates="prescriptions")
    medicines: Mapped[List["Medicine"]] = relationship("Medicine", back_populates="prescription", cascade="all, delete-orphan")
    qr_tokens: Mapped[List["PrescriptionQR"]] = relationship("PrescriptionQR", back_populates="prescription")
    sources: Mapped[List["PrescriptionSource"]] = relationship("PrescriptionSource", back_populates="prescription")


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dosage: Mapped[str] = mapped_column(String, nullable=False)
    times_per_day: Mapped[list[time]] = mapped_column(ARRAY(TIME), nullable=False)
    instructions: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="medicines")
    dose_logs: Mapped[List["DoseLog"]] = relationship("DoseLog", back_populates="medicine", cascade="all, delete-orphan")
