from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.appointment import Appointment
from ..models.clinic import Clinic
from ..models.doctor import Doctor
from ..models.user import User
import os

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

SUPER_ADMIN_KEY = os.getenv("SUPER_ADMIN_KEY", "apna-bhagalpur-super-admin-2024")

def verify_super_admin(x_api_key: str = Header(None)):
    if x_api_key != SUPER_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@router.get("/overview")
@limiter.limit("20/minute")
async def get_overview(request: Request, db: Session = Depends(get_db), _: bool = Depends(verify_super_admin)):
    today = date.today()
    start_date = today - timedelta(days=29)
    
    total_clinics = db.query(Clinic).count()
    total_doctors = db.query(Doctor).count()
    
    total_patients = db.query(Appointment).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today
    ).count()
    
    total_completed = db.query(Appointment).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.status == "completed"
    ).count()
    
    total_absent = db.query(Appointment).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.status == "absent"
    ).count()
    
    absent_rate = round((total_absent / total_patients * 100), 1) if total_patients > 0 else 0
    
    return {
        "total_clinics": total_clinics,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_completed": total_completed,
        "total_absent": total_absent,
        "absent_rate": absent_rate,
        "period": "Last 30 Days"
    }


@router.get("/clinic-performance")
@limiter.limit("20/minute")
async def get_clinic_performance(request: Request, db: Session = Depends(get_db), _: bool = Depends(verify_super_admin)):
    today = date.today()
    start_date = today - timedelta(days=29)
    
    clinics = db.query(Clinic).all()
    performance = []
    
    for clinic in clinics:
        total = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today
        ).count()
        
        completed = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.status == "completed"
        ).count()
        
        absent = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.status == "absent"
        ).count()
        
        waiting = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.status == "waiting"
        ).count()
        
        rate = round((completed / total * 100), 1) if total > 0 else 0
        
        performance.append({
            "id": clinic.id,
            "name": clinic.name,
            "emoji": clinic.emoji,
            "total": total,
            "completed": completed,
            "absent": absent,
            "waiting": waiting,
            "completion_rate": rate
        })
    
    return sorted(performance, key=lambda x: x["total"], reverse=True)


@router.get("/daily-stats")
@limiter.limit("20/minute")
async def get_daily_stats(request: Request, db: Session = Depends(get_db), _: bool = Depends(verify_super_admin)):
    today = date.today()
    start_date = today - timedelta(days=29)
    
    daily = []
    current = start_date
    while current <= today:
        total = db.query(Appointment).filter(
            Appointment.appointment_date == current
        ).count()
        
        completed = db.query(Appointment).filter(
            Appointment.appointment_date == current,
            Appointment.status == "completed"
        ).count()
        
        absent = db.query(Appointment).filter(
            Appointment.appointment_date == current,
            Appointment.status == "absent"
        ).count()
        
        daily.append({
            "date": str(current),
            "day": current.strftime("%a"),
            "total": total,
            "completed": completed,
            "absent": absent
        })
        current += timedelta(days=1)
    
    return daily


@router.get("/recent")
@limiter.limit("20/minute")
async def get_recent(request: Request, db: Session = Depends(get_db), _: bool = Depends(verify_super_admin)):
    appointments = db.query(Appointment).order_by(
        Appointment.appointment_date.desc(),
        Appointment.slot_number.desc()
    ).limit(20).all()
    
    return [{
        "id": a.id,
        "patient_name": a.patient_name,
        "clinic_name": a.clinic.name if a.clinic else "N/A",
        "doctor_name": a.doctor.name if a.doctor else "N/A",
        "appointment_date": str(a.appointment_date),
        "time_slot": a.time_slot,
        "status": a.status,
        "booking_type": a.booking_type
    } for a in appointments]