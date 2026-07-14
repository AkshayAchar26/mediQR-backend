from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date

class PatientRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=5, max_length=20)
    dob: Optional[date] = None

class PatientResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    dob: Optional[date]
    created_at: datetime

    
    class Config:
        from_attributes = True

class PatientUpdateRequest(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
