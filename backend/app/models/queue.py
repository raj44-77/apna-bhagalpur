from sqlalchemy import Column, Integer, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class QueueState(Base):
    __tablename__ = "queue_state"
    
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    appointment_date = Column(Date, nullable=False)
    current_slot_number = Column(Integer, default=0)
    total_patients_served = Column(Integer, default=0)
    total_absent = Column(Integer, default=0)
    total_walkins = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    last_updated = Column(DateTime)
    
    clinic = relationship("Clinic", back_populates="queue_states")