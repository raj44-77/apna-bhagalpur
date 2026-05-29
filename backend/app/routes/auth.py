from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
import re
import random
from ..database import get_db
from ..models.user import User
from ..models.clinic import Clinic

router = APIRouter()

# JWT Config
SECRET_KEY = "apna-bhagalpur-jwt-secret-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Store reset codes temporarily
reset_codes = {}


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
        if not validate_email(data.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Get clinic name if user is a clinic admin
        clinic_name = None
        if user.clinic_id:
            clinic = db.query(Clinic).filter(Clinic.id == user.clinic_id).first()
            if clinic:
                clinic_name = clinic.name
        
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
                "clinic_name": clinic_name,
                "age": user.age,
                "gender": user.gender,
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
        if not validate_name(data.get("name", "")):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        
        if not validate_email(data.get("email", "")):
            raise HTTPException(status_code=400, detail="Invalid email format. Example: user@email.com")
        
        if not validate_phone(data.get("phone", "")):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        
        if not validate_password(data.get("password", "")):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if db.query(User).filter(User.phone == data["phone"]).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        hashed_password = hash_password(data["password"])
        
        age = data.get("age")
        if age and str(age).isdigit():
            age = int(age)
        else:
            age = None
        
        user = User(
            name=data["name"].strip(),
            email=data["email"].strip().lower(),
            phone=data["phone"].strip(),
            password=hashed_password,
            user_type="patient",
            age=age,
            gender=data.get("gender", "").strip() or None
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
        if not validate_name(data.get("name", "")):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        
        if not validate_email(data.get("email", "")):
            raise HTTPException(status_code=400, detail="Invalid email format. Example: clinic@email.com")
        
        if not validate_phone(data.get("phone", "")):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        
        if not validate_password(data.get("password", "")):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
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


@router.post("/forgot-password")
async def forgot_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        
        if not validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        if not validate_phone(phone):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        
        user = db.query(User).filter(
            User.email == email,
            User.phone == phone
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="No account found with this email and phone")
        
        reset_code = str(random.randint(100000, 999999))
        reset_codes[email] = {
            "code": reset_code,
            "user_id": user.id,
            "expires": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return {
            "message": "Reset code generated",
            "reset_code": reset_code,
            "email": email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip().lower()
        code = data.get("code", "").strip()
        new_password = data.get("new_password", "")
        
        if not validate_password(new_password):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        stored = reset_codes.get(email)
        if not stored:
            raise HTTPException(status_code=400, detail="No reset code found. Please request again")
        
        if stored["code"] != code:
            raise HTTPException(status_code=400, detail="Invalid reset code")
        
        if datetime.utcnow() > stored["expires"]:
            del reset_codes[email]
            raise HTTPException(status_code=400, detail="Reset code expired. Please request again")
        
        user = db.query(User).filter(User.id == stored["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.password = hash_password(new_password)
        db.commit()
        
        del reset_codes[email]
        
        return {"message": "Password reset successful! You can now login."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))