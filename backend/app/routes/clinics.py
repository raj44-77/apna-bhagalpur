from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import date, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.clinic import Clinic
from ..models.doctor import Doctor
from ..models.appointment import Appointment

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

CLINIC_EMOJIS = {1: "🏥", 2: "☀️", 3: "🏨", 4: "❤️", 5: "💊", 6: "🏥", 7: "🏥", 8: "🏥", 9: "🏥", 10: "☀️", 11: "🏨", 12: "🏥", 13: "🏥"}

@router.get("/")
@limiter.limit("60/minute")
async def get_clinics(request: Request, db: Session = Depends(get_db)):
    clinics = db.query(Clinic).all()
    return [{"id": c.id, "name": c.name, "address": c.address, "phone": c.phone, "email": c.email, "timing": c.timing, "clinic_type": c.clinic_type, "emoji": CLINIC_EMOJIS.get(c.id, "🏥"), "is_active": c.is_active, "doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in c.doctors]} for c in clinics]

@router.get("/rankings")
async def get_clinic_rankings(days: int = 30, db: Session = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=days)
    clinics = db.query(Clinic).all()
    rankings = []
    for clinic in clinics:
        total = db.query(Appointment).filter(Appointment.clinic_id == clinic.id, Appointment.appointment_date >= start_date, Appointment.appointment_date <= today).count()
        completed = db.query(Appointment).filter(Appointment.clinic_id == clinic.id, Appointment.appointment_date >= start_date, Appointment.appointment_date <= today, Appointment.status == "completed").count()
        if total > 0:
            completion_rate = round((completed / total) * 100, 1)
            score = round(total * 0.6 + completion_rate * 0.3 + completed * 0.1, 1)
        else:
            completion_rate = 0
            score = 0
        rankings.append({"id": clinic.id, "name": clinic.name, "emoji": CLINIC_EMOJIS.get(clinic.id, "🏥"), "address": clinic.address, "total_bookings": total, "completed": completed, "completion_rate": completion_rate, "score": score})
    rankings.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
        if i == 0: r["medal"] = "🥇"
        elif i == 1: r["medal"] = "🥈"
        elif i == 2: r["medal"] = "🥉"
        else: r["medal"] = str(i + 1)
    return rankings[:10]

@router.get("/{clinic_id}")
async def get_clinic(clinic_id: int, db: Session = Depends(get_db)):
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    if not clinic: raise HTTPException(status_code=404, detail="Not found")
    return {"id": clinic.id, "name": clinic.name, "address": clinic.address, "phone": clinic.phone, "email": clinic.email, "timing": clinic.timing, "clinic_type": clinic.clinic_type, "emoji": CLINIC_EMOJIS.get(clinic.id, "🏥"), "is_active": clinic.is_active, "doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in clinic.doctors]}

@router.get("/{clinic_id}/doctors")
async def get_doctors(clinic_id: int, db: Session = Depends(get_db)):
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    return [{"id": d.id, "name": d.name, "specialty": d.specialty, "max_slots": d.max_slots, "consultation_fee": float(d.consultation_fee) if d.consultation_fee else 0, "is_available": d.is_available} for d in doctors]