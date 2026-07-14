from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, time

class MedicineCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    dosage: str = Field(..., min_length=1)
    times_per_day: List[time] = Field(..., min_length=1)
    instructions: Optional[str] = None

class PrescriptionCreateRequest(BaseModel):
    till_date: date
    notes: Optional[str] = None
    medicines: List[MedicineCreateRequest] = Field(..., min_length=1)

class MedicineResponse(BaseModel):
    id: UUID
    prescription_id: UUID
    name: str
    dosage: str
    times_per_day: List[time]
    instructions: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PrescriptionResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: Optional[UUID]
    hospital_or_clinic: str
    till_date: date
    notes: Optional[str]
    status: str
    created_at: datetime
    medicines: List[MedicineResponse] = []
    
    class Config:
        from_attributes = True

class PrescriptionListResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    patient_id: Optional[UUID]
    hospital_or_clinic: str
    till_date: date
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
