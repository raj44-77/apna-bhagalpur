from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import date, datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..models.appointment import Appointment
from ..models.queue import QueueState
from .auth import require_clinic_admin, require_clinic_owner

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def to_minutes(time_str):
    if not time_str: return 9999
    try:
        t, period = time_str.strip().split()
        h, m = map(int, t.split(':'))
        if period == 'PM' and h != 12: h += 12
        if period == 'AM' and h == 12: h = 0
        return h * 60 + m
    except: return 9999


@router.get('/status/{clinic_id}')
@limiter.limit("30/minute")
async def get_queue_status(request: Request, clinic_id: int, appointment_date: str = None, db: Session = Depends(get_db)):
    today = appointment_date if appointment_date else str(date.today())
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    if not queue: return {'clinic_id': clinic_id, 'current_slot': 0, 'appointments': []}
    
    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id, 
        Appointment.appointment_date == today
    ).all()
    appointments.sort(key=lambda a: to_minutes(a.time_slot))
    
    return {
        'clinic_id': clinic_id, 'current_slot': queue.current_slot_number,
        'total_served': queue.total_patients_served, 'total_absent': queue.total_absent,
        'total_walkins': queue.total_walkins, 'is_paused': queue.is_paused,
        'appointments': [{'id': a.id, 'slot_number': a.slot_number, 'patient_name': a.patient_name, 'status': a.status, 'booking_type': a.booking_type, 'time_slot': a.time_slot, 'booking_id': a.booking_id} for a in appointments]
    }


@router.post('/pause/{clinic_id}')
@limiter.limit("10/minute")
async def toggle_pause(request: Request, clinic_id: int, user: dict = Depends(require_clinic_admin), owner_clinic_id: int = Depends(require_clinic_owner), db: Session = Depends(get_db)):
    if owner_clinic_id is not None and owner_clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Access denied. This is not your clinic.")
    
    today = date.today()
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    if not queue: queue = QueueState(clinic_id=clinic_id, appointment_date=today, current_slot_number=0, is_paused=False); db.add(queue); db.flush()
    queue.is_paused = not queue.is_paused
    db.commit()
    return {'message': 'Queue paused' if queue.is_paused else 'Queue resumed', 'is_paused': queue.is_paused}


@router.get('/live-tracking/{clinic_id}')
@limiter.limit("30/minute")
async def live_tracking(request: Request, clinic_id: int, slot_number: int, db: Session = Depends(get_db)):
    today = date.today()
    appointment = db.query(Appointment).filter(Appointment.clinic_id == clinic_id, Appointment.slot_number == slot_number, Appointment.appointment_date == today).first()
    if not appointment: raise HTTPException(status_code=404, detail='Not found')
    queue = db.query(QueueState).filter(QueueState.clinic_id == clinic_id, QueueState.appointment_date == today).first()
    current_slot = queue.current_slot_number if queue else 0
    ahead = max(0, appointment.slot_number - current_slot)
    return {'your_slot': appointment.slot_number, 'current_slot': current_slot, 'queue_ahead': ahead, 'estimated_wait_minutes': ahead * 15, 'status': appointment.status, 'booking_id': appointment.booking_id, 'patient_name': appointment.patient_name, 'time_slot': appointment.time_slot}