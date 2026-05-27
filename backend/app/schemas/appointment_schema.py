from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class AppointmentCreate(BaseModel):
    clinic_id: int
    doctor_id: int
    patient_name: str
    patient_phone: str
    appointment_date: date
    time_slot: str

class WalkInCreate(BaseModel):
    clinic_id: int
    doctor_id: int
    patient_name: str
    patient_phone: Optional[str] = ""

class AppointmentResponse(BaseModel):
    id: int
    booking_id: str
    clinic_id: int
    doctor_id: int
    patient_name: str
    patient_phone: str
    appointment_date: date
    time_slot: str
    slot_number: int
    booking_type: str
    status: str
    clinic_name: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueueResponse(BaseModel):
    clinic_id: int
    current_slot: int
    total_waiting: int
    appointments: list