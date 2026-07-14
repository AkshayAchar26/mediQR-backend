from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class DoctorRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=5, max_length=20)
    hospital_or_clinic: str = Field(..., min_length=2, max_length=200)
    expertise: List[str] = Field(default_factory=list)

class DoctorResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    hospital_or_clinic: str
    expertise: List[str]
    certificate_url: Optional[str]
    verified_status: str
    created_at: datetime

    
    class Config:
        from_attributes = True

class DoctorUpdateRequest(BaseModel):
    name: Optional[str] = None
    hospital_or_clinic: Optional[str] = None
    expertise: Optional[List[str]] = None
    certificate_url: Optional[str] = None
    verified_status: Optional[str] = None
