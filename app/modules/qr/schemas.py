from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.modules.prescriptions.schemas import PrescriptionListResponse

class QRClaimRequest(BaseModel):
    token: str = Field(..., min_length=10)

class QRResponse(BaseModel):
    id: UUID
    prescription_id: UUID
    token: str
    status: str
    expires_at: datetime
    claimed_by: Optional[UUID]
    claimed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class QRClaimResponse(BaseModel):
    prescription_id: UUID
    message: str = "Prescription claimed successfully"

class HistoryQRGenerateRequest(BaseModel):
    scope: str = Field(default="all", description="'all' or 'selected'")
    scope_prescription_ids: Optional[List[UUID]] = None

class HistoryQRClaimRequest(BaseModel):
    token: str = Field(..., min_length=10)

class PatientHistoryQRResponse(BaseModel):
    id: UUID
    patient_id: UUID
    token: str
    scope: str
    scope_prescription_ids: Optional[List[UUID]]
    status: str
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class HistoryAccessLogResponse(BaseModel):
    id: UUID
    patient_history_qr_id: UUID
    doctor_id: UUID
    accessed_at: datetime
    # Optionally include doctor details if needed, but doctor_id is enough for now
    
    class Config:
        from_attributes = True

class HistoryQRClaimResponse(BaseModel):
    patient_id: UUID
    prescriptions: List[PrescriptionListResponse]
