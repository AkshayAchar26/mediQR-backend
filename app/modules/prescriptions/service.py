from app.modules.prescriptions.repository import PrescriptionRepository
from app.modules.prescriptions.schemas import PrescriptionCreateRequest
from app.db.models.prescriptions import Prescription, Medicine
from app.db.models.doses import DoseLog
from app.modules.doctors.repository import DoctorRepository
from app.core.exceptions import NotFoundError, AppError
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import List

class PrescriptionService:
    def __init__(self, repository: PrescriptionRepository, doctor_repository: DoctorRepository):
        self.repository = repository
        self.doctor_repository = doctor_repository

    async def create_prescription(self, doctor_id: UUID, data: PrescriptionCreateRequest) -> Prescription:
        doctor = await self.doctor_repository.get_by_id(doctor_id)
        if not doctor:
            raise NotFoundError("Doctor not found.")
            
        if data.till_date < datetime.now().date():
            raise AppError(code="INVALID_DATE", message="till_date cannot be in the past.")

        # Create Prescription object
        prescription = Prescription(
            doctor_id=doctor_id,
            hospital_or_clinic=doctor.hospital_or_clinic, # Snapshot
            till_date=data.till_date,
            notes=data.notes,
            status="unclaimed"
        )
        
        # Attach medicines and pre-generate dose logs
        medicines_list = []
        for med_data in data.medicines:
            medicine = Medicine(
                name=med_data.name,
                dosage=med_data.dosage,
                times_per_day=med_data.times_per_day,
                instructions=med_data.instructions
            )
            
            # Generate dose logs for this medicine up to till_date
            dose_logs = []
            current_date = datetime.now().date()
            while current_date <= data.till_date:
                for t in med_data.times_per_day:
                    scheduled_datetime = datetime.combine(current_date, t).replace(tzinfo=timezone.utc)
                    # Don't schedule for times that have already passed today
                    if scheduled_datetime > datetime.now(timezone.utc):
                        dose_logs.append(DoseLog(scheduled_datetime=scheduled_datetime))
                current_date += timedelta(days=1)
                
            medicine.dose_logs = dose_logs
            medicines_list.append(medicine)
            
        prescription.medicines = medicines_list
        return await self.repository.create(prescription)

    async def get_prescription(self, prescription_id: UUID, user_id: UUID, role: str) -> Prescription:
        prescription = await self.repository.get_by_id(prescription_id)
        if not prescription:
            raise NotFoundError("Prescription not found.")
            
        # Access control
        if role == "doctor" and prescription.doctor_id != user_id:
            raise NotFoundError("Prescription not found.") # Hide existence
        if role == "patient" and prescription.patient_id != user_id:
            raise NotFoundError("Prescription not found.")

        return prescription

    async def list_doctor_prescriptions(self, doctor_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        return await self.repository.list_by_doctor(doctor_id, limit, offset)

    async def list_patient_prescriptions(self, patient_id: UUID, limit: int = 20, offset: int = 0) -> List[Prescription]:
        return await self.repository.list_by_patient(patient_id, limit, offset)

    async def get_history_for_doctor(self, patient_id: UUID, scope: str, scope_prescription_ids: List[UUID] | None) -> List[Prescription]:
        """
        Special method that bypasses the normal doctor_id check.
        Only called by QR service after a valid history QR claim.
        """
        if scope == "selected" and scope_prescription_ids:
            prescriptions = await self.repository.get_by_ids(scope_prescription_ids)
            # Ensure they actually belong to the patient
            return [p for p in prescriptions if p.patient_id == patient_id]
        else:
            # Return all history (no pagination limit for this special share feature, or a very high limit)
            return await self.repository.list_by_patient(patient_id, limit=1000, offset=0)
