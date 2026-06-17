from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.appointment import Appointment
from ..models.clinic import Clinic
from ..models.doctor import Doctor
from ..models.queue import QueueState

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class BookingData(BaseModel):
    clinic_id: int
    doctor_id: int
    patient_name: str
    patient_phone: str
    appointment_date: str
    time_slot: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None


def to_minutes(time_str):
    if not time_str: return 9999
    try:
        t, period = time_str.strip().split()
        h, m = map(int, t.split(':'))
        if period == 'PM' and h != 12: h += 12
        if period == 'AM' and h == 12: h = 0
        return h * 60 + m
    except: return 9999


@router.post("/book")
@limiter.limit("10/minute")
async def book_appointment(request: Request, data: BookingData, db: Session = Depends(get_db)):
    try:
        clinic = db.query(Clinic).filter(Clinic.id == data.clinic_id).first()
        if not clinic: raise HTTPException(status_code=404, detail="Clinic not found")
        doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
        if not doctor: raise HTTPException(status_code=404, detail="Doctor not found")
        
        queue_check = db.query(QueueState).filter(QueueState.clinic_id == data.clinic_id, QueueState.appointment_date == data.appointment_date).first()
        if queue_check and queue_check.is_locked: raise HTTPException(status_code=400, detail="Bookings are closed for this date")
        
        count = db.query(Appointment).filter(Appointment.clinic_id == data.clinic_id, Appointment.appointment_date == data.appointment_date).count()
        slot_num = count + 1
        booking_id = f"B{slot_num:03d}"
        
        appointment = Appointment(
            booking_id=booking_id, clinic_id=data.clinic_id, doctor_id=data.doctor_id,
            patient_name=data.patient_name, patient_phone=data.patient_phone,
            patient_age=data.patient_age, patient_gender=data.patient_gender,
            appointment_date=data.appointment_date, time_slot=data.time_slot,
            slot_number=slot_num, booking_type="online", status="waiting"
        )
        db.add(appointment); db.flush()
        
        queue = db.query(QueueState).filter(QueueState.clinic_id == data.clinic_id, QueueState.appointment_date == data.appointment_date).first()
        if not queue: queue = QueueState(clinic_id=data.clinic_id, doctor_id=data.doctor_id, appointment_date=data.appointment_date, current_slot_number=0); db.add(queue); db.flush()
        
        existing_current = db.query(Appointment).filter(Appointment.clinic_id == data.clinic_id, Appointment.appointment_date == data.appointment_date, Appointment.status == "current").first()
        if not existing_current:
            all_apts = db.query(Appointment).filter(Appointment.clinic_id == data.clinic_id, Appointment.appointment_date == data.appointment_date).all()
            all_apts.sort(key=lambda a: to_minutes(a.time_slot))
            if all_apts:
                all_apts[0].status = "current"
                queue.current_slot_number = all_apts[0].slot_number
        
        db.commit(); db.refresh(appointment)
        
        return {
            "id": appointment.id, "booking_id": appointment.booking_id, "clinic_id": appointment.clinic_id,
            "doctor_id": appointment.doctor_id, "patient_name": appointment.patient_name,
            "patient_phone": appointment.patient_phone, "patient_age": appointment.patient_age,
            "patient_gender": appointment.patient_gender, "appointment_date": str(appointment.appointment_date),
            "time_slot": appointment.time_slot, "slot_number": appointment.slot_number,
            "booking_type": appointment.booking_type, "status": appointment.status,
            "clinic_name": clinic.name, "doctor_name": doctor.name, "created_at": str(datetime.now())
        }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/revisit")
@limiter.limit("10/minute")
async def book_revisit(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        clinic_id = data.get("clinic_id")
        doctor_id = data.get("doctor_id")
        patient_name = data.get("patient_name")
        patient_phone = data.get("patient_phone")
        appointment_date = data.get("appointment_date")
        time_slot = data.get("time_slot")
        
        fifteen_days_ago = date.today() - timedelta(days=15)
        original_visit = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.patient_phone == patient_phone,
            Appointment.status == "completed",
            Appointment.booking_type != "revisit",
            Appointment.appointment_date >= fifteen_days_ago
        ).order_by(Appointment.appointment_date.desc()).first()
        
        if not original_visit:
            raise HTTPException(status_code=400, detail="No eligible visit found. Revisit is valid only within 15 days of your last visit.")
        
        already_revisited = db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.patient_phone == patient_phone,
            Appointment.booking_type == "revisit",
            Appointment.appointment_date >= original_visit.appointment_date
        ).first()
        
        if already_revisited:
            raise HTTPException(status_code=400, detail="You have already used your revisit. Only one revisit is allowed per visit.")
        
        count = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == appointment_date).count()
        slot_num = count + 1
        booking_id = f"R{clinic_id}{slot_num:03d}"
        
        appointment = Appointment(
            booking_id=booking_id, clinic_id=clinic_id, doctor_id=doctor_id,
            patient_name=patient_name, patient_phone=patient_phone,
            appointment_date=appointment_date, time_slot=time_slot,
            slot_number=slot_num, booking_type="revisit", status="waiting"
        )
        db.add(appointment); db.flush()
        
        queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == appointment_date).first()
        if not queue: queue = QueueState(clinic_id=clinic_id, doctor_id=doctor_id, appointment_date=appointment_date, current_slot_number=0); db.add(queue); db.flush()
        
        existing_current = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == appointment_date, Appointment.status == "current").first()
        if not existing_current:
            all_apts = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == appointment_date).all()
            all_apts.sort(key=lambda a: to_minutes(a.time_slot))
            if all_apts:
                all_apts[0].status = "current"
                queue.current_slot_number = all_apts[0].slot_number
        
        db.commit(); db.refresh(appointment)
        
        return {
            "id": appointment.id, "booking_id": appointment.booking_id,
            "slot_number": appointment.slot_number, "booking_type": "revisit",
            "status": appointment.status, "time_slot": appointment.time_slot,
            "clinic_name": appointment.clinic.name if appointment.clinic else None,
            "message": "Revisit booked successfully! No payment needed."
        }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.get("/track/{clinic_id}")
async def track_queue(clinic_id: int, slot_number: int, appointment_date: str = None, db: Session = Depends(get_db)):
    track_date = appointment_date if appointment_date else str(date.today())
    appointment = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.slot_number == slot_number, Appointment.appointment_date == track_date).first()
    if not appointment: raise HTTPException(status_code=404, detail="Appointment not found")
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == track_date).first()
    current_slot = queue.current_slot_number if queue else 0
    ahead = max(0, appointment.slot_number - current_slot)
    wait_minutes = ahead * 15; hours, minutes = wait_minutes // 60, wait_minutes % 60
    wait_str = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
    if appointment.status == "completed": status_msg, alert = "Complete", "success"
    elif ahead == 0 and appointment.status == "current": status_msg, alert = "Your turn now!", "warning"
    elif ahead <= 3: status_msg, alert = "Almost there!", "warning"
    else: status_msg, alert = "In queue", "info"
    return {"your_slot": appointment.slot_number, "current_slot": current_slot, "queue_ahead": ahead, "estimated_wait_minutes": wait_minutes, "estimated_wait_string": wait_str, "status": appointment.status, "status_message": status_msg, "alert_type": alert, "booking_id": appointment.booking_id, "patient_name": appointment.patient_name, "time_slot": appointment.time_slot, "appointment_date": str(appointment.appointment_date)}


@router.get("/track-by-booking/{clinic_id}")
async def track_by_booking(clinic_id: int, booking_id: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.booking_id == booking_id).first()
    if not appointment: raise HTTPException(status_code=404, detail="Booking not found")
    all_apts = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == appointment.appointment_date, Appointment.status.in_(["waiting", "current"])).all()
    all_apts.sort(key=lambda a: to_minutes(a.time_slot))
    ahead = 0
    for a in all_apts:
        if a.booking_id == booking_id: break
        ahead += 1
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == appointment.appointment_date).first()
    current_slot = queue.current_slot_number if queue else 0
    wait_minutes = ahead * 15; hours, minutes = wait_minutes // 60, wait_minutes % 60
    wait_str = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
    if appointment.status == "completed": status_msg, alert = "Complete", "success"
    elif ahead == 0 and appointment.status == "current": status_msg, alert = "Your turn now!", "warning"
    elif ahead <= 3: status_msg, alert = "Almost there!", "warning"
    else: status_msg, alert = "In queue", "info"
    return {
        "booking_id": appointment.booking_id, "slot_number": appointment.slot_number,
        "queue_position": ahead + 1, "queue_ahead": ahead,
        "time_slot": appointment.time_slot, "status": appointment.status,
        "status_message": status_msg, "alert_type": alert,
        "patient_name": appointment.patient_name,
        "clinic_name": appointment.clinic.name if appointment.clinic else None,
        "current_slot": current_slot, "estimated_wait_minutes": wait_minutes,
        "estimated_wait_string": wait_str
    }


@router.get("/my-bookings")
@limiter.limit("30/minute")
async def my_bookings(request: Request, phone: str, db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.patient_phone == phone).order_by(Appointment.appointment_date.desc()).all()
    result = []
    for a in appointments:
        is_revisit_available = False
        if a.status == "completed" and a.booking_type != "revisit":
            days_since = (date.today() - a.appointment_date).days if a.appointment_date else 999
            if days_since <= 15:
                already = db.query(Appointment).filter(
                    Appointment.clinic_id == a.clinic_id,
                    Appointment.patient_phone == phone,
                    Appointment.booking_type == "revisit",
                    Appointment.appointment_date >= a.appointment_date
                ).first()
                if not already:
                    is_revisit_available = True
        
        result.append({
            "id": a.id, "booking_id": a.booking_id, "clinic_id": a.clinic_id,
            "doctor_id": a.doctor_id, "patient_name": a.patient_name,
            "patient_phone": a.patient_phone, "appointment_date": str(a.appointment_date),
            "time_slot": a.time_slot, "slot_number": a.slot_number,
            "booking_type": a.booking_type, "status": a.status,
            "is_revisit_available": is_revisit_available,
            "clinic_name": a.clinic.name if a.clinic else None,
            "doctor_name": a.doctor.name if a.doctor else None,
            "created_at": str(a.created_at)
        })
    return result