from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import bcrypt
from ..database import get_db
from ..models.user import User

router = APIRouter()


class LoginData(BaseModel):
    email: str
    password: str


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


@router.post("/login")
async def login(data: LoginData, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {
            "access_token": "token-" + str(user.id),
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
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if db.query(User).filter(User.phone == data["phone"]).first():
            raise HTTPException(status_code=400, detail="Phone already registered")
        
        # Hash the password
        hashed_password = hash_password(data["password"])
        
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
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
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        hashed_password = hash_password(data["password"])
        
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
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