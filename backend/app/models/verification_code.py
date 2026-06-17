from sqlalchemy import Column, Integer, String, DateTime, Text
from ..database import Base

class VerificationCode(Base):
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False)
    code_type = Column(String(50), default="email_verify")
    user_data = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime)