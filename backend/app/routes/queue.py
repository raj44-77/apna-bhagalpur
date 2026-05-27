from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from ..database import get_db
from ..models.appointment import Appointment
from ..models.queue import QueueState

router = APIRouter()


@router.get('/status/{clinic_id}')
async def get_queue_status(clinic_id: int, db: Session = Depends(get_db)):
    today = date.today()
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    if not queue:
        return {'clinic_id': clinic_id, 'current_slot': 0, 'appointments': []}
    
    appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.appointment_date == today
    ).order_by(Appointment.slot_number).all()
    
    return {
        'clinic_id': clinic_id,
        'current_slot': queue.current_slot_number,
        'total_served': queue.total_patients_served,
        'total_absent': queue.total_absent,
        'total_walkins': queue.total_walkins,
        'is_paused': queue.is_paused,
        'appointments': [{
            'id': a.id, 'slot_number': a.slot_number,
            'patient_name': a.patient_name, 'status': a.status,
            'booking_type': a.booking_type, 'time_slot': a.time_slot
        } for a in appointments]
    }


@router.post('/pause/{clinic_id}')
async def toggle_pause(clinic_id: int, db: Session = Depends(get_db)):
    today = date.today()
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    if not queue:
        # Create queue if not exists
        queue = QueueState(
            clinic_id=clinic_id,
            appointment_date=today,
            current_slot_number=0,
            is_paused=False
        )
        db.add(queue)
        db.flush()
    
    queue.is_paused = not queue.is_paused
    db.commit()
    
    return {
        'message': 'Queue paused' if queue.is_paused else 'Queue resumed',
        'is_paused': queue.is_paused
    }


@router.get('/live-tracking/{clinic_id}')
async def live_tracking(clinic_id: int, slot_number: int, db: Session = Depends(get_db)):
    today = date.today()
    appointment = db.query(Appointment).filter(
        Appointment.clinic_id == clinic_id,
        Appointment.slot_number == slot_number,
        Appointment.appointment_date == today
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail='Appointment not found')
    
    queue = db.query(QueueState).filter(
        QueueState.clinic_id == clinic_id,
        QueueState.appointment_date == today
    ).first()
    
    current_slot = queue.current_slot_number if queue else 0
    ahead = max(0, appointment.slot_number - current_slot)
    wait_minutes = ahead * 15
    
    return {
        'your_slot': appointment.slot_number,
        'current_slot': current_slot,
        'queue_ahead': ahead,
        'estimated_wait_minutes': wait_minutes,
        'status': appointment.status,
        'booking_id': appointment.booking_id,
        'patient_name': appointment.patient_name,
        'time_slot': appointment.time_slot
    }