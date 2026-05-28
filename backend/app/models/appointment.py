from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(10), nullable=True)
    appointment_date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    slot_number = Column(Integer, nullable=False)
    booking_type = Column(String(20), default="online")
    status = Column(String(20), default="waiting")
    check_in_time = Column(DateTime, nullable=True)
    consultation_start_time = Column(DateTime, nullable=True)
    consultation_end_time = Column(DateTime, nullable=True)
    actual_consultation_time = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    user = relationship("User", back_populates="appointments")
    clinic = relationship("Clinic", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment")