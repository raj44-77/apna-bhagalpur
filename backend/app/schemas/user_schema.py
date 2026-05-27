from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    email: str
    phone: str
    password: str

class ClinicRegister(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    clinic_id: int

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    user_type: str
    clinic_id: Optional[int] = None
    clinic_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse