from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from pydantic import BaseModel
from ..database import get_db
from ..models.appointment import Appointment
from ..models.queue import QueueState
from ..models.clinic import Clinic
from ..models.doctor import Doctor
from .websocket import broadcast

router = APIRouter()


class WalkInData(BaseModel):
    clinic_id: int = 0
    doctor_id: int
    patient_name: str
    patient_phone: str = ""


@router.post("/next-slot/{clinic_id}")
async def next_slot(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    current = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today,
        Appointment.status == "current"
    ).first()
    
    if current:
        current.status = "completed"
    
    next_patient = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today,
        Appointment.status == "waiting"
    ).order_by(Appointment.slot_number).first()
    
    if next_patient:
        next_patient.status = "current"
        queue = db.query(QueueState).filter(
            QueueState.clinic_id == clinic_id,
            QueueState.appointment_date == today
        ).first()
        if queue:
            queue.current_slot_number = next_patient.slot_number
            queue.total_patients_served += 1
        db.commit()
        
        await broadcast(clinic_id, {
            "action": "next_slot",
            "current_slot": next_patient.slot_number,
            "message": f"Now serving slot #{next_patient.slot_number}"
        })
        
        return {"message": f"Now serving slot #{next_patient.slot_number}", "current_slot": next_patient.slot_number}
    
    db.commit()
    return {"message": "No more patients"}


@router.post("/mark-absent/{clinic_id}")
async def mark_absent(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    current = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today,
        Appointment.status == "current"
    ).first()
    
    if not current:
        raise HTTPException(status_code=404, detail="No current patient")
    
    current.status = "absent"
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    if queue:
        queue.total_absent += 1
    
    db.commit()
    
    await broadcast(clinic_id, {
        "action": "mark_absent",
        "slot": current.slot_number,
        "message": f"Slot #{current.slot_number} marked absent"
    })
    
    return await next_slot(clinic_id, appointment_date, db)


@router.post("/add-walkin/{clinic_id}")
async def add_walkin(clinic_id: int, data: WalkInData, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    
    count = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today
    ).count()
    
    booking_id = f"WLK{clinic_id}{today.replace('-','')}{count + 1:03d}"
    
    appointment = Appointment(
        booking_id=booking_id,
        clinic_id=clinic_id,
        doctor_id=data.doctor_id,
        patient_name=data.patient_name,
        patient_phone=data.patient_phone or "",
        appointment_date=today,
        time_slot=datetime.now().strftime("%I:%M %p"),
        slot_number=count + 1,
        booking_type="walkin",
        status="waiting"
    )
    
    db.add(appointment)
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    if not queue:
        queue = QueueState(
            clinic_id=clinic_id,
            doctor_id=data.doctor_id,
            appointment_date=today,
            current_slot_number=0
        )
        db.add(queue)
    queue.total_walkins += 1
    
    db.commit()
    db.refresh(appointment)
    
    await broadcast(clinic_id, {
        "action": "add_walkin",
        "slot": appointment.slot_number,
        "patient": data.patient_name,
        "message": f"Walk-in added: {data.patient_name}"
    })
    
    return {
        "id": appointment.id,
        "slot_number": appointment.slot_number,
        "patient_name": appointment.patient_name,
        "status": appointment.status
    }


@router.get("/dashboard/{clinic_id}")
async def get_dashboard(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    print(f"DEBUG Dashboard: clinic={clinic_id}, date={today}")
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today
    ).order_by(Appointment.slot_number).all()
    
    print(f"DEBUG Dashboard: Found {len(appointments)} appointments")
    
    current = None
    for a in appointments:
        if a.status == "current":
            current = a
            break
    
    return {
        "appointment_date": today,
        "is_locked": queue.is_locked if queue else False,
        "queue": {
            "current_slot": queue.current_slot_number if queue else 0,
            "total_served": queue.total_patients_served if queue else 0,
            "total_absent": queue.total_absent if queue else 0,
            "total_walkins": queue.total_walkins if queue else 0
        },
        "current_patient": {
            "slot_number": current.slot_number if current else None,
            "name": current.patient_name if current else None,
            "booking_type": current.booking_type if current else None,
            "time_slot": current.time_slot if current else None
        } if current else None,
        "appointments": [{
            "id": a.id,
            "booking_id": a.booking_id,
            "slot_number": a.slot_number,
            "patient_name": a.patient_name,
            "patient_phone": a.patient_phone,
            "booking_type": a.booking_type,
            "time_slot": a.time_slot,
            "status": a.status,
            "doctor_name": a.doctor.name if a.doctor else None
        } for a in appointments],
        "stats": {
            "total": len(appointments),
            "completed": len([a for a in appointments if a.status == "completed"]),
            "waiting": len([a for a in appointments if a.status == "waiting"]),
            "absent": len([a for a in appointments if a.status == "absent"])
        }
    }


@router.post("/lock/{clinic_id}")
async def lock_queue(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    if not queue:
        queue = QueueState(
            clinic_id=clinic_id,
            appointment_date=today,
            current_slot_number=0,
            is_locked=True
        )
        db.add(queue)
    else:
        queue.is_locked = True
    
    db.commit()
    return {"message": f"Queue locked for {today}", "is_locked": True, "appointment_date": today}


@router.post("/unlock/{clinic_id}")
async def unlock_queue(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    if queue:
        queue.is_locked = False
        db.commit()
    
    return {"message": f"Queue unlocked for {today}", "is_locked": False, "appointment_date": today}


@router.get("/is-locked/{clinic_id}")
async def is_queue_locked(clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    return {"appointment_date": today, "is_locked": queue.is_locked if queue else False}