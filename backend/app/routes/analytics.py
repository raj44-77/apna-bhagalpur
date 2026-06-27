from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from datetime import date, datetime, timedelta
from ..database import get_db
from ..models.appointment import Appointment
from ..models.doctor import Doctor
from ..models.clinic import Clinic
from .auth import require_clinic_admin

router = APIRouter()


@router.get("/overview/{clinic_id}")
async def get_overview(clinic_id: int, days: int = 7, user: dict = Depends(require_clinic_admin), db: Session = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # SINGLE QUERY with conditional aggregation
    stats = db.query(
        func.count(Appointment.id).label('total'),
        func.sum(case((Appointment.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((Appointment.status == 'absent', 1), else_=0)).label('absent'),
        func.sum(case((Appointment.status == 'waiting', 1), else_=0)).label('waiting'),
        func.avg(
            case((Appointment.actual_consultation_time > 0, Appointment.actual_consultation_time), else_=None)
        ).label('avg_time')
    ).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today
    ).first()
    
    today_count = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today
    ).count()
    
    total = stats.total or 0
    completed = stats.completed or 0
    absent = stats.absent or 0
    waiting = stats.waiting or 0
    avg_time = float(stats.avg_time) if stats.avg_time else 0
    
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
        "avg_consultation_minutes": round(avg_time, 1),
        "completion_rate": round((completed / total * 100), 1) if total > 0 else 0
    }


@router.get("/daily/{clinic_id}")
async def get_daily_stats(clinic_id: int, days: int = 7, user: dict = Depends(require_clinic_admin), db: Session = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # SINGLE QUERY with GROUP BY date
    daily_stats = db.query(
        Appointment.appointment_date,
        func.count(Appointment.id).label('total'),
        func.sum(case((Appointment.status == 'completed', 1), else_=0)).label('completed')
    ).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today
    ).group_by(Appointment.appointment_date).order_by(Appointment.appointment_date).all()
    
    # Build lookup
    stats_map = {str(s.appointment_date): s for s in daily_stats}
    
    daily_data = []
    current_date = start_date
    while current_date <= today:
        s = stats_map.get(str(current_date))
        daily_data.append({
            "date": str(current_date),
            "day_name": current_date.strftime("%a"),
            "total": s.total if s else 0,
            "completed": s.completed if s else 0
        })
        current_date += timedelta(days=1)
    
    return daily_data


@router.get("/doctors/{clinic_id}")
async def get_doctor_stats(clinic_id: int, days: int = 7, user: dict = Depends(require_clinic_admin), db: Session = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    # SINGLE QUERY with GROUP BY doctor instead of N+1 loop
    stats = db.query(
        Appointment.doctor_id,
        func.count(Appointment.id).label('total'),
        func.sum(case((Appointment.status == 'completed', 1), else_=0)).label('completed'),
        func.avg(
            case((Appointment.actual_consultation_time > 0, Appointment.actual_consultation_time), else_=None)
        ).label('avg_time')
    ).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= today
    ).group_by(Appointment.doctor_id).all()
    
    # Build lookup
    stats_map = {s.doctor_id: s for s in stats}
    
    # Get doctors for this clinic
    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic_id).all()
    
    doctor_stats = []
    for doc in doctors:
        s = stats_map.get(doc.id)
        total = s.total if s else 0
        completed = s.completed if s else 0
        avg_time = float(s.avg_time) if s and s.avg_time else 0
        
        doctor_stats.append({
            "id": doc.id,
            "name": doc.name,
            "specialty": doc.specialty,
            "total_patients": total,
            "completed": completed,
            "avg_consultation_minutes": round(avg_time, 1),
            "completion_rate": round((completed / total * 100), 1) if total > 0 else 0
        })
    
    return sorted(doctor_stats, key=lambda x: x["total_patients"], reverse=True)


@router.get("/hourly/{clinic_id}")
async def get_hourly_stats(clinic_id: int, days: int = 7, user: dict = Depends(require_clinic_admin), db: Session = Depends(get_db)):
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
async def get_recent_appointments(clinic_id: int, limit: int = 20, user: dict = Depends(require_clinic_admin), db: Session = Depends(get_db)):
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