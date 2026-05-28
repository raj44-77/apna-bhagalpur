from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_type = Column(String(20), default="patient")
    clinic_id = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    appointments = relationship("Appointment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")