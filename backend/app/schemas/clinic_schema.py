from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    max_slots: int
    consultation_fee: float
    is_available: bool
    
    class Config:
        from_attributes = True

class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str
    phone: Optional[str]
    email: Optional[str]
    timing: str
    clinic_type: Optional[str]
    emoji: str
    is_active: bool
    doctors: List[DoctorResponse] = []
    
    class Config:
        from_attributes = True