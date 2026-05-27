from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.clinic import Clinic
from ..models.doctor import Doctor

router = APIRouter()

# Hardcoded emojis since MySQL doesn't support them well
CLINIC_EMOJIS = {
    1: "🏥",
    2: "☀️",
    3: "🏨",
    4: "❤️",
    5: "💊"
}

@router.get("/")
async def get_clinics(db: Session = Depends(get_db)):
    try:
        clinics = db.query(Clinic).all()
        result = []
        for clinic in clinics:
            doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic.id).all()
            result.append({
                "id": clinic.id,
                "name": clinic.name,
                "address": clinic.address,
                "phone": clinic.phone,
                "email": clinic.email,
                "timing": clinic.timing,
                "clinic_type": clinic.clinic_type,
                "emoji": CLINIC_EMOJIS.get(clinic.id, "🏥"),
                "is_active": clinic.is_active,
                "doctors": [{
                    "id": d.id,
                    "name": d.name,
                    "specialty": d.specialty,
                    "max_slots": d.max_slots,
                    "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0,
                    "is_available": d.is_available
                } for d in doctors]
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{clinic_id}")
async def get_clinic(clinic_id: int, db: Session = Depends(get_db)):
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    return {
        "id": clinic.id,
        "name": clinic.name,
        "address": clinic.address,
        "phone": clinic.phone,
        "email": clinic.email,
        "timing": clinic.timing,
        "clinic_type": clinic.clinic_type,
        "emoji": CLINIC_EMOJIS.get(clinic.id, "🏥"),
        "is_active": clinic.is_active,
        "doctors": [{
            "id": d.id,
            "name": d.name,
            "specialty": d.specialty,
            "max_slots": d.max_slots,
            "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0,
            "is_available": d.is_available
        } for d in doctors]
    }

@router.get("/{clinic_id}/doctors")
async def get_doctors(clinic_id: int, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    return [{
        "id": d.id,
        "name": d.name,
        "specialty": d.specialty,
        "max_slots": d.max_slots,
        "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0,
        "is_available": d.is_available
    } for d in doctors]