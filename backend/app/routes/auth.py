from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
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
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate real JWT token
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
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        if db.query(User).filter(User.phone == data["phone"]).first():
            raise HTTPException(status_code=400, detail="Phone already registered")
        
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