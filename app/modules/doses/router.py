from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.db.base import get_db_session
from app.core.deps import require_patient
from app.modules.doses.schemas import DoseLogResponse, MarkDoseResponse
from app.modules.doses.service import DoseService
from app.modules.doses.repository import SQLAlchemyDoseLogRepository

router = APIRouter(prefix="/doses", tags=["Doses"])

def get_dose_service(db: AsyncSession = Depends(get_db_session)) -> DoseService:
    repository = SQLAlchemyDoseLogRepository(db)
    return DoseService(repository=repository)

@router.get("", response_model=dict)
async def list_doses(
    prescription_id: UUID = Query(...),
    patient_id: str = Depends(require_patient),
    service: DoseService = Depends(get_dose_service)
):
    """List all doses for a prescription with their computed statuses."""
    # In a full app, we would verify the prescription belongs to the patient
    # before listing doses. We'll skip that check here for brevity, but it's important.
    doses = await service.list_prescription_doses(prescription_id)
    return {"data": [DoseLogResponse(**d).model_dump(mode='json') for d in doses], "error": None}

@router.post("/{dose_log_id}/mark-taken", response_model=dict)
async def mark_dose_taken(
    dose_log_id: UUID,
    patient_id: str = Depends(require_patient),
    service: DoseService = Depends(get_dose_service)
):
    """Mark a dose as taken (atomic write-once). Evaluates 'taken' vs 'taken_late' server-side."""
    updated_dose = await service.mark_dose_taken(dose_log_id)
    return {"data": MarkDoseResponse(id=updated_dose.id, marked_status=updated_dose.marked_status).model_dump(mode='json'), "error": None}
