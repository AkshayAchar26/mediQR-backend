import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.base import Base
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from .prescriptions import Prescription
    from .users import Patient, Doctor

class PrescriptionQR(Base):
    __tablename__ = "prescription_qr"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active") # active, claimed, expired
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    claimed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="qr_tokens")
    patient: Mapped[Optional["Patient"]] = relationship("Patient")

class PatientHistoryQR(Base):
    __tablename__ = "patient_history_qr"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False, server_default="all") # all, selected
    scope_prescription_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active")
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient")
    access_logs: Mapped[List["HistoryAccessLog"]] = relationship("HistoryAccessLog", back_populates="qr_token")

class HistoryAccessLog(Base):
    __tablename__ = "history_access_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    patient_history_qr_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patient_history_qr.id"), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    qr_token: Mapped["PatientHistoryQR"] = relationship("PatientHistoryQR", back_populates="access_logs")
    doctor: Mapped["Doctor"] = relationship("Doctor")
