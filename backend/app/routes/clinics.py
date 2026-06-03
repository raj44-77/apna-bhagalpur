from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.clinic import Clinic
from ..models.doctor import Doctor

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

CLINIC_EMOJIS = {1: "🏥", 2: "☀️", 3: "🏨", 4: "❤️", 5: "💊", 6: "🏥", 7: "🏥", 8: "🏥", 9: "🏥", 10: "☀️", 11: "🏨", 12: "🏥", 13: "🏥"}

@router.get("/")
@limiter.limit("60/minute")
async def get_clinics(request: Request, db: Session = Depends(get_db)):
    clinics = db.query(Clinic).all()
    return [{"id": c.id, "name": c.name, "address": c.address, "phone": c.phone, "email": c.email, "timing": c.timing, "clinic_type": c.clinic_type, "emoji": CLINIC_EMOJIS.get(c.id, "🏥"), "is_active": c.is_active, "doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in c.doctors]} for c in clinics]

@router.get("/{clinic_id}")
async def get_clinic(clinic_id: int, db: Session = Depends(get_db)):
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic: raise HTTPException(status_code=404, detail="Not found")
    return {"id": clinic.id, "name": clinic.name, "address": clinic.address, "phone": clinic.phone, "email": clinic.email, "timing": clinic.timing, "clinic_type": clinic.clinic_type, "emoji": CLINIC_EMOJIS.get(clinic.id, "🏥"), "is_active": clinic.is_active, "doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in clinic.doctors]}

@router.get("/{clinic_id}/doctors")
async def get_doctors(clinic_id: int, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in doctors]