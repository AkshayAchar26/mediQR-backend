from app.modules.doses.repository import DoseLogRepository
from app.db.models.doses import DoseLog
from app.core.exceptions import NotFoundError, ConflictError, AppError
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import List

class DoseService:
    def __init__(self, repository: DoseLogRepository):
        self.repository = repository
        self.grace_hours = 2

    def compute_status(self, dose_log: DoseLog) -> str:
        """
        Computes the real-time status of a dose.
        """
        if dose_log.marked_status:
            return dose_log.marked_status
        if datetime.now(timezone.utc) > dose_log.scheduled_datetime + timedelta(hours=self.grace_hours):
            return "missed"
        return "pending"

    async def list_prescription_doses(self, prescription_id: UUID) -> List[dict]:
        """
        Returns a list of dose logs with their computed statuses.
        """
        doses = await self.repository.list_for_prescription(prescription_id)
        
        results = []
        for dose in doses:
            # We construct a dict because computed_status is not a DB column
            dose_dict = {
                "id": dose.id,
                "medicine_id": dose.medicine_id,
                "scheduled_datetime": dose.scheduled_datetime,
                "marked_status": dose.marked_status,
                "marked_at": dose.marked_at,
                "created_at": dose.created_at,
                "computed_status": self.compute_status(dose)
            }
            results.append(dose_dict)
        return results

    async def mark_dose_taken(self, dose_log_id: UUID) -> DoseLog:
        dose_log = await self.repository.get_by_id(dose_log_id)
        if not dose_log:
            raise NotFoundError("Dose log not found.")
            
        if dose_log.marked_status:
            raise ConflictError("This dose has already been marked.")
            
        now = datetime.now(timezone.utc)
        
        # Decide if taken or taken_late based on grace window
        if now <= dose_log.scheduled_datetime + timedelta(hours=self.grace_hours):
            status = "taken"
        else:
            status = "taken_late"
            
        updated_dose = await self.repository.mark_taken(dose_log_id, status, now)
        if not updated_dose:
             # If the atomic update returned None, it means it was modified concurrently
             raise ConflictError("Failed to mark dose. It may have been updated already.")
             
        return updated_dose
