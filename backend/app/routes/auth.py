from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
import re
from ..database import get_db
from ..models.user import User

router = APIRouter()

# JWT Config
SECRET_KEY = "apna-bhagalpur-jwt-secret-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


class LoginData(BaseModel):
    email: str
    password: str


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone - exactly 10 digits"""
    return phone.isdigit() and len(phone) == 10


def validate_password(password: str) -> bool:
    """Validate password - at least 6 characters"""
    return len(password) >= 6


def validate_name(name: str) -> bool:
    """Validate name - at least 3 characters"""
    return len(name.strip()) >= 3


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: int, user_type: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": user_type,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
async def login(data: LoginData, db: Session = Depends(get_db)):
    try:
        # Validate email format
        if not validate_email(data.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        access_token = create_access_token(user.id, user.user_type)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "user_type": user.user_type,
                "clinic_id": user.clinic_id,
                "clinic_name": None,
                "is_active": bool(user.is_active),
                "created_at": str(user.created_at)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/patient")
async def register_patient(data: dict, db: Session = Depends(get_db)):
    try:
        # Validate inputs
        if not validate_name(data.get("name", "")):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        
        if not validate_email(data.get("email", "")):
            raise HTTPException(status_code=400, detail="Invalid email format. Example: user@email.com")
        
        if not validate_phone(data.get("phone", "")):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        
        if not validate_password(data.get("password", "")):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Check existing
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if db.query(User).filter(User.phone == data["phone"]).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        hashed_password = hash_password(data["password"])
        
        user = User(
            name=data["name"].strip(),
            email=data["email"].strip().lower(),
            phone=data["phone"].strip(),
            password=hashed_password,
            user_type="patient"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"id": user.id, "name": user.name, "email": user.email}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/clinic")
async def register_clinic(data: dict, db: Session = Depends(get_db)):
    try:
        # Validate inputs
        if not validate_name(data.get("name", "")):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        
        if not validate_email(data.get("email", "")):
            raise HTTPException(status_code=400, detail="Invalid email format. Example: clinic@email.com")
        
        if not validate_phone(data.get("phone", "")):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        
        if not validate_password(data.get("password", "")):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Check existing
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password(data["password"])
        
        user = User(
            name=data["name"].strip(),
            email=data["email"].strip().lower(),
            phone=data["phone"].strip(),
            password=hashed_password,
            user_type="clinic",
            clinic_id=data["clinic_id"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"id": user.id, "name": user.name, "email": user.email}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))