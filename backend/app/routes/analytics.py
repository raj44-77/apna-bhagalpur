from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime, timedelta
from ..database import get_db
from ..models.appointment import Appointment
from ..models.doctor import Doctor
from ..models.clinic import Clinic

router = APIRouter()


@router.get("/overview/{clinic_id}")
async def get_overview(clinic_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get overview stats for last N days"""
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # Total appointments in period
    total = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today
    ).count()
    
    # Status breakdown
    completed = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.status == "completed"
    ).count()
    
    absent = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.status == "absent"
    ).count()
    
    waiting = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.status == "waiting"
    ).count()
    
    # Today's count
    today_count = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today
    ).count()
    
    # Average consultation time
    avg_time = db.query(func.avg(Appointment.actual_consultation_time)).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today,
        Appointment.actual_consultation_time > 0
    ).scalar() or 0
    
    return {
        "period": f"Last {days} days",
        "start_date": str(start_date),
        "end_date": str(today),
        "total_patients": total,
        "completed": completed,
        "absent": absent,
        "waiting": waiting,
        "absent_rate": round((absent / total * 100), 1) if total > 0 else 0,
        "today_count": today_count,
        "avg_consultation_minutes": round(float(avg_time), 1),
        "completion_rate": round((completed / total * 100), 1) if total > 0 else 0
    }


@router.get("/daily/{clinic_id}")
async def get_daily_stats(clinic_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get daily breakdown for charts"""
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    daily_data = []
    current_date = start_date
    while current_date <= today:
        day_total = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == current_date
        ).count()
        
        day_completed = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date == current_date,
            Appointment.status == "completed"
        ).count()
        
        daily_data.append({
            "date": str(current_date),
            "day_name": current_date.strftime("%a"),
            "total": day_total,
            "completed": day_completed
        })
        current_date += timedelta(days=1)
    
    return daily_data


@router.get("/doctors/{clinic_id}")
async def get_doctor_stats(clinic_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get per-doctor performance"""
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    
    doctor_stats = []
    for doc in doctors:
        total = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today
        ).count()
        
        completed = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.status == "completed"
        ).count()
        
        avg_time = db.query(func.avg(Appointment.actual_consultation_time)).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.doctor_id == doc.id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.actual_consultation_time > 0
        ).scalar() or 0
        
        doctor_stats.append({
            "id": doc.id,
            "name": doc.name,
            "specialty": doc.specialty,
            "total_patients": total,
            "completed": completed,
            "avg_consultation_minutes": round(float(avg_time), 1),
            "completion_rate": round((completed / total * 100), 1) if total > 0 else 0
        })
    
    return sorted(doctor_stats, key=lambda x: x["total_patients"], reverse=True)


@router.get("/hourly/{clinic_id}")
async def get_hourly_stats(clinic_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get hourly distribution for peak hours"""
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    hourly_data = []
    hours = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]
    
    for hour in hours:
        count = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= today,
            Appointment.time_slot.like(f"{hour}%")
        ).count()
        
        hourly_data.append({
            "hour": hour,
            "count": count
        })
    
    total = sum(h["count"] for h in hourly_data) or 1
    
    for h in hourly_data:
        h["percentage"] = round((h["count"] / total * 100), 1)
    
    return hourly_data


@router.get("/recent/{clinic_id}")
async def get_recent_appointments(clinic_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Get recent appointments"""
    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id
    ).order_by(Appointment.appointment_date.desc(), Appointment.slot_number.desc()).limit(limit).all()
    
    return [{
        "id": a.id,
        "booking_id": a.booking_id,
        "patient_name": a.patient_name,
        "doctor_name": a.doctor.name if a.doctor else "N/A",
        "appointment_date": str(a.appointment_date),
        "time_slot": a.time_slot,
        "status": a.status,
        "booking_type": a.booking_type
    } for a in appointments]