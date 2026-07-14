import uuid
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .prescriptions import Prescription

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hospital_or_clinic: Mapped[str] = mapped_column(String, nullable=False)
    expertise: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    certificate_url: Mapped[str | None] = mapped_column(String, nullable=True)
    verified_status: Mapped[str] = mapped_column(String, nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    # Relationships
    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="patient")

class EmailOTP(Base):
    __tablename__ = "email_otps"

    email: Mapped[str] = mapped_column(String, primary_key=True)
    otp: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

