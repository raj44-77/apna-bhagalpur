from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base
import enum
class NotificationType(str, enum.Enum):
    BOOKING = 'booking'
    REMINDER = 'reminder'
    SLOT_READY = 'slot_ready'
    DELAY = 'delay'
    ABSENT = 'absent'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id', ondelete='CASCADE'), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    type = Column(Enum(NotificationType))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime)
    user = relationship('User', back_populates='notifications')
    appointment = relationship('Appointment', back_populates='notifications')
