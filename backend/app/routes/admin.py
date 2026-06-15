from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.appointment import Appointment
from ..models.queue import QueueState
from ..models.clinic import Clinic
from ..models.doctor import Doctor
from .websocket import broadcast

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def to_minutes(time_str):
    """Convert time like '09:30 AM' to minutes since midnight"""
    if not time_str: return 0
    try:
        t, period = time_str.strip().split()
        h, m = map(int, t.split(':'))
        if period == 'PM' and h != 12: h += 12
        if period == 'AM' and h == 12: h = 0
        return h * 60 + m
    except: return 0


@router.post("/next-slot/{clinic_id}")
@limiter.limit("20/minute")
async def next_slot(request: Request, clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    current = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today, Appointment.status == "current").first()
    if current: current.status = "completed"
    # Find next by EARLIEST time
    next_patient = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today, Appointment.status == "waiting").order_by(Appointment.time_slot, Appointment.id).first()
    if next_patient:
        next_patient.status = "current"
        queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
        if queue: queue.current_slot_number = next_patient.slot_number; queue.total_patients_served += 1
        db.commit()
        await broadcast(clinic_id, {"action": "next_slot", "current_slot": next_patient.slot_number, "message": f"Now serving: {next_patient.patient_name} ({next_patient.time_slot})"})
        return {"message": f"Now serving {next_patient.patient_name} at {next_patient.time_slot}", "current_slot": next_patient.slot_number}
    db.commit()
    return {"message": "No more patients"}


@router.post("/mark-absent/{clinic_id}")
@limiter.limit("20/minute")
async def mark_absent(request: Request, clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    current = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today, Appointment.status == "current").first()
    if not current: raise HTTPException(status_code=404, detail="No current patient")
    current.status = "absent"
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    if queue: queue.total_absent += 1
    db.commit()
    await broadcast(clinic_id, {"action": "mark_absent", "slot": current.slot_number, "message": f"Marked absent: {current.patient_name}"})
    return await next_slot(request, clinic_id, appointment_date, db)


@router.post("/add-walkin/{clinic_id}")
@limiter.limit("20/minute")
async def add_walkin(request: Request, clinic_id: int, doctor_id: int, patient_name: str, patient_phone: str = "", appointment_date: str = None, db: Session = Depends(get_db)):
    try:
        today = appointment_date if appointment_date else str(date.today())
        count = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today).count()
        slot_num = count + 1
        booking_id = f"WLK{clinic_id}{today.replace('-','')}{slot_num:03d}"
        ist = timezone(timedelta(hours=5, minutes=30))
        ist_time = datetime.now(ist).strftime("%I:%M %p")
        appointment = Appointment(booking_id=booking_id, clinic_id=clinic_id, doctor_id=doctor_id, patient_name=patient_name, patient_phone=patient_phone or "", appointment_date=today, time_slot=ist_time, slot_number=slot_num, booking_type="walkin", status="waiting")
        db.add(appointment)
        queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
        if not queue: queue = QueueState(clinic_id=clinic_id, doctor_id=doctor_id, appointment_date=today, current_slot_number=0); db.add(queue); db.flush()
        queue.total_walkins += 1
        db.commit(); db.refresh(appointment)
        await broadcast(clinic_id, {"action": "add_walkin", "slot": appointment.slot_number, "patient": patient_name, "message": f"Walk-in: {patient_name}"})
        return {"id": appointment.id, "slot_number": appointment.slot_number, "patient_name": appointment.patient_name, "status": appointment.status}
    except Exception as e: db.rollback(); raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{clinic_id}")
@limiter.limit("30/minute")
async def get_dashboard(request: Request, clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    appointments = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today).order_by(Appointment.time_slot, Appointment.id).all()
    current = None
    for a in appointments:
        if a.status == "current": current = a; break
    return {
        "appointment_date": today, "is_locked": queue.is_locked if queue else False,
        "queue": {"current_slot": queue.current_slot_number if queue else 0, "total_served": queue.total_patients_served if queue else 0, "total_absent": queue.total_absent if queue else 0, "total_walkins": queue.total_walkins if queue else 0},
        "current_patient": {"slot_number": current.slot_number if current else None, "name": current.patient_name if current else None, "booking_type": current.booking_type if current else None, "time_slot": current.time_slot if current else None, "booking_id": current.booking_id if current else None} if current else None,
        "appointments": [{"id": a.id, "booking_id": a.booking_id, "slot_number": a.slot_number, "patient_name": a.patient_name, "patient_phone": a.patient_phone, "booking_type": a.booking_type, "time_slot": a.time_slot, "status": a.status, "doctor_name": a.doctor.name if a.doctor else None} for a in appointments],
        "stats": {"total": len(appointments), "completed": len([a for a in appointments if a.status == "completed"]), "waiting": len([a for a in appointments if a.status == "waiting"]), "absent": len([a for a in appointments if a.status == "absent"])}
    }


@router.post("/lock/{clinic_id}")
async def lock_queue(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    if not queue: queue = QueueState(clinic_id=clinic_id, appointment_date=today, current_slot_number=0, is_locked=True); db.add(queue)
    else: queue.is_locked = True
    db.commit()
    return {"message": f"Queue locked for {today}", "is_locked": True}


@router.post("/unlock/{clinic_id}")
async def unlock_queue(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    if queue: queue.is_locked = False; db.commit()
    return {"message": f"Queue unlocked for {today}", "is_locked": False}


@router.get("/is-locked/{clinic_id}")
async def is_queue_locked(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    return {"appointment_date": today, "is_locked": queue.is_locked if queue else False}


@router.get("/absentees/{clinic_id}")
async def get_absentees(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    absentees = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.appointment_date == today, Appointment.status == "absent").order_by(Appointment.slot_number).all()
    return [{"id": a.id, "booking_id": a.booking_id, "slot_number": a.slot_number, "patient_name": a.patient_name, "patient_phone": a.patient_phone, "time_slot": a.time_slot} for a in absentees]


@router.post("/start-treatment/{appointment_id}")
async def start_treatment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment: raise HTTPException(status_code=404, detail="Not found")
    if appointment.status != "absent": raise HTTPException(status_code=400, detail="Patient is not absent")
    max_slot = db.query(func.max(Appointment.slot_number)).filter(Appointment.clinic_id == appointment.clinic_id, Appointment.appointment_date == appointment.appointment_date).scalar() or 0
    appointment.status = "waiting"; appointment.slot_number = max_slot + 1
    db.commit()
    return {"message": f"{appointment.patient_name} added back to queue", "new_slot": appointment.slot_number}


@router.post("/reschedule/{appointment_id}")
async def reschedule_appointment(appointment_id: int, new_date: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment: raise HTTPException(status_code=404, detail="Not found")
    if appointment.status != "absent": raise HTTPException(status_code=400, detail="Patient is not absent")
    max_slot = db.query(func.max(Appointment.slot_number)).filter(Appointment.clinic_id == appointment.clinic_id, Appointment.appointment_date == new_date).scalar() or 0
    appointment.appointment_date = new_date; appointment.status = "waiting"; appointment.slot_number = max_slot + 1
    db.commit()
    return {"message": f"Rescheduled to {new_date}", "new_slot": appointment.slot_number}