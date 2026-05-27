from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.user import User

router = APIRouter()


class LoginData(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(data: LoginData, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(
            User.email == data.email,
            User.password == data.password
        ).first()
        
        if not user:
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
        
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            password=data["password"],
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
        
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            password=data["password"],
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