import secrets
from app.modules.qr.repository import PrescriptionQRRepository, PatientHistoryQRRepository
from app.modules.prescriptions.repository import PrescriptionRepository
from app.modules.prescriptions.service import PrescriptionService
from app.db.models.qr import PrescriptionQR, PatientHistoryQR, HistoryAccessLog
from app.db.models.prescriptions import Prescription
from app.core.exceptions import ConflictError, NotFoundError, AppError
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta, timezone

class QRService:
    def __init__(self, repository: PrescriptionQRRepository, prescription_repo: PrescriptionRepository, history_repository: PatientHistoryQRRepository, prescription_service: PrescriptionService):
        self.repository = repository
        self.prescription_repo = prescription_repo
        self.history_repository = history_repository
        self.prescription_service = prescription_service

    def _generate_token(self) -> str:
        # Generates a secure random token (e.g. 16 characters)
        return secrets.token_urlsafe(12)

    async def generate_prescription_qr(self, doctor_id: UUID, prescription_id: UUID) -> PrescriptionQR:
        prescription = await self.prescription_repo.get_by_id(prescription_id)
        if not prescription or prescription.doctor_id != doctor_id:
            raise NotFoundError("Prescription not found or unauthorized.")
            
        if prescription.status != "unclaimed":
            raise AppError(code="ALREADY_CLAIMED", message="Prescription has already been claimed.", status_code=400)

        # Check for duplicate active QR
        active_qr = await self.repository.get_active_for_prescription(prescription_id)
        if active_qr:
            return active_qr

        # Create new QR code valid for 24 hours
        qr = PrescriptionQR(
            prescription_id=prescription_id,
            token=self._generate_token(),
            status="active",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        return await self.repository.create(qr)

    async def claim_prescription_qr(self, patient_id: UUID, token: str) -> UUID:
        """
        Attempts to claim a QR token atomically. Returns the prescription ID if successful.
        """
        prescription_id = await self.repository.claim_qr(token, patient_id)
        if not prescription_id:
            raise ConflictError("QR token is invalid, expired, or already claimed.")
        return prescription_id

    async def generate_history_qr(self, patient_id: UUID, scope: str, scope_prescription_ids: Optional[List[UUID]]) -> PatientHistoryQR:
        qr = PatientHistoryQR(
            patient_id=patient_id,
            token=self._generate_token(),
            scope=scope,
            scope_prescription_ids=scope_prescription_ids,
            status="active",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        return await self.history_repository.create(qr)

    async def claim_history_qr(self, doctor_id: UUID, token: str) -> tuple[UUID, List[Prescription]]:
        qr = await self.history_repository.get_active_by_token(token)
        if not qr:
            raise ConflictError("History QR token is invalid or expired.")

        # Log access
        log = HistoryAccessLog(
            patient_history_qr_id=qr.id,
            doctor_id=doctor_id
        )
        await self.history_repository.log_access(log)

        # Fetch history
        prescriptions = await self.prescription_service.get_history_for_doctor(
            patient_id=qr.patient_id,
            scope=qr.scope,
            scope_prescription_ids=qr.scope_prescription_ids
        )
        return qr.patient_id, prescriptions

    async def get_access_logs(self, patient_id: UUID) -> List[HistoryAccessLog]:
        return await self.history_repository.get_access_logs(patient_id)
