from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class DoseLogResponse(BaseModel):
    id: UUID
    medicine_id: UUID
    scheduled_datetime: datetime
    marked_status: Optional[str] # taken or taken_late, null means not acted on
    marked_at: Optional[datetime]
    created_at: datetime
    computed_status: str # 'taken', 'taken_late', 'missed', 'pending'
    
    class Config:
        from_attributes = True

class MarkDoseResponse(BaseModel):
    id: UUID
    marked_status: str
    message: str = "Dose marked successfully"
