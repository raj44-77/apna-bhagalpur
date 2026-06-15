from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import bcrypt, re, random
from ..database import get_db
from ..models.user import User
from ..models.clinic import Clinic

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# JWT Config
SECRET_KEY = "apna-bhagalpur-jwt-secret-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# Temporary storage
reset_codes = {}
email_codes = {}


class LoginData(BaseModel):
    email: str  # Can be email OR phone
    password: str


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    return phone.isdigit() and len(phone) == 10

def validate_password(password: str) -> bool:
    return len(password) >= 6

def validate_name(name: str) -> bool:
    return len(name.strip()) >= 3

def is_valid_indian_mobile(phone: str) -> bool:
    if not phone.isdigit() or len(phone) != 10:
        return False
    if phone[0] not in '6789':
        return False
    spam_patterns = [
        '1111111111', '2222222222', '3333333333', '4444444444',
        '5555555555', '6666666666', '7777777777', '8888888888',
        '9999999999', '0000000000', '1234567890', '0987654321',
        '1122334455', '1234512345', '9876598765', '9000000000'
    ]
    if phone in spam_patterns:
        return False
    return True

def is_email(value: str) -> bool:
    return '@' in value and '.' in value

def is_phone(value: str) -> bool:
    return value.isdigit() and len(value) == 10

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: int, user_type: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "type": user_type, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginData, db: Session = Depends(get_db)):
    try:
        login_value = data.email.strip().lower()
        
        # Find user by email OR phone
        if is_email(login_value):
            user = db.query(User).filter(User.email == login_value).first()
        elif is_phone(login_value):
            user = db.query(User).filter(User.phone == login_value).first()
        else:
            raise HTTPException(status_code=400, detail="Enter a valid email or 10-digit phone number")
        
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        clinic_name = None
        if user.clinic_id:
            clinic = db.query(Clinic).filter(Clinic.id == user.clinic_id).first()
            if clinic: clinic_name = clinic.name
        
        access_token = create_access_token(user.id, user.user_type)
        
        return {
            "access_token": access_token, "token_type": "bearer",
            "user": {
                "id": user.id, "name": user.name, "email": user.email,
                "phone": user.phone, "user_type": user.user_type,
                "clinic_id": user.clinic_id, "clinic_name": clinic_name,
                "age": user.age, "gender": user.gender,
                "is_active": bool(user.is_active), "created_at": str(user.created_at)
            }
        }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/patient")
@limiter.limit("3/hour")
async def register_patient(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        login_value = data.get("login", "").strip()
        password = data.get("password", "")
        name = data.get("name", "").strip()
        age = data.get("age")
        gender = data.get("gender")
        
        if not validate_name(name):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        if not validate_password(password):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        if is_email(login_value):
            if not validate_email(login_value):
                raise HTTPException(status_code=400, detail="Invalid email format")
            email = login_value.lower()
            if db.query(User).filter(User.email == email).first():
                raise HTTPException(status_code=400, detail="Email already registered")
            # Send verification code
            code = str(random.randint(100000, 999999))
            email_codes[email] = {"code": code, "name": name, "password": hash_password(password), "age": int(age) if age and str(age).isdigit() else None, "gender": gender, "expires": datetime.utcnow() + timedelta(minutes=10)}
            return {"message": "Verification code sent to your email", "code": code, "email": email, "step": "verify_email"}
            
        elif is_phone(login_value):
            if not is_valid_indian_mobile(login_value):
                raise HTTPException(status_code=400, detail="Invalid phone number. Enter a valid 10-digit Indian mobile number.")
            if db.query(User).filter(User.phone == login_value).first():
                raise HTTPException(status_code=400, detail="Phone already registered")
            hashed = hash_password(password)
            user = User(name=name, email=f"ph{login_value}@user.apnabhagalpur.com", phone=login_value, password=hashed, user_type="patient", age=int(age) if age and str(age).isdigit() else None, gender=gender or None)
            db.add(user); db.commit(); db.refresh(user)
            return {"id": user.id, "name": user.name, "message": "Registration successful! You can login now."}
        else:
            raise HTTPException(status_code=400, detail="Enter a valid email or 10-digit phone number")
            
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-email")
async def verify_email(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip().lower()
        code = data.get("code", "").strip()
        
        stored = email_codes.get(email)
        if not stored:
            raise HTTPException(status_code=400, detail="No verification code found. Please register again.")
        if stored["code"] != code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        if datetime.utcnow() > stored["expires"]:
            del email_codes[email]
            raise HTTPException(status_code=400, detail="Code expired. Please register again.")
        
        user = User(
            name=stored["name"], email=email,
            phone=f"em{random.randint(100000,999999)}",
            password=stored["password"], user_type="patient",
            age=stored.get("age"), gender=stored.get("gender")
        )
        db.add(user); db.commit(); db.refresh(user)
        del email_codes[email]
        
        return {"id": user.id, "name": user.name, "email": user.email, "message": "Email verified! Account created. You can login now."}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/clinic")
@limiter.limit("3/hour")
async def register_clinic(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        if not validate_name(data.get("name", "")):
            raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        if not validate_email(data.get("email", "")):
            raise HTTPException(status_code=400, detail="Invalid email format")
        if not validate_phone(data.get("phone", "")):
            raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        if not validate_password(data.get("password", "")):
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = hash_password(data["password"])
        user = User(name=data["name"].strip(), email=data["email"].strip().lower(), phone=data["phone"].strip(), password=hashed, user_type="clinic", clinic_id=data["clinic_id"])
        db.add(user); db.commit(); db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip().lower()
        phone = data.get("phone", "").strip()
        if not validate_email(email): raise HTTPException(status_code=400, detail="Invalid email format")
        if not validate_phone(phone): raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        user = db.query(User).filter(User.email == email, User.phone == phone).first()
        if not user: raise HTTPException(status_code=404, detail="No account found")
        reset_code = str(random.randint(100000, 999999))
        reset_codes[email] = {"code": reset_code, "user_id": user.id, "expires": datetime.utcnow() + timedelta(minutes=10)}
        return {"message": "Reset code generated", "reset_code": reset_code, "email": email}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip().lower()
        code = data.get("code", "").strip()
        new_password = data.get("new_password", "")
        if not validate_password(new_password): raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        stored = reset_codes.get(email)
        if not stored: raise HTTPException(status_code=400, detail="No reset code found")
        if stored["code"] != code: raise HTTPException(status_code=400, detail="Invalid reset code")
        if datetime.utcnow() > stored["expires"]: del reset_codes[email]; raise HTTPException(status_code=400, detail="Code expired")
        user = db.query(User).filter(User.id == stored["user_id"]).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        user.password = hash_password(new_password); db.commit()
        del reset_codes[email]
        return {"message": "Password reset successful"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.put("/update-profile")
async def update_profile(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = data.get("user_id")
        if not user_id: raise HTTPException(status_code=400, detail="User ID required")
        user = db.query(User).filter(User.id == user_id).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        if not validate_name(data.get("name", "")): raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        if not validate_email(data.get("email", "")): raise HTTPException(status_code=400, detail="Invalid email format")
        if not validate_phone(data.get("phone", "")): raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        existing_email = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if existing_email: raise HTTPException(status_code=400, detail="Email already in use")
        existing_phone = db.query(User).filter(User.phone == data["phone"], User.id != user_id).first()
        if existing_phone: raise HTTPException(status_code=400, detail="Phone already in use")
        user.name = data["name"].strip(); user.email = data["email"].strip().lower(); user.phone = data["phone"].strip()
        user.age = int(data["age"]) if data.get("age") and str(data["age"]).isdigit() else None
        user.gender = data.get("gender") or None
        db.commit(); db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email, "message": "Profile updated"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.put("/change-password")
async def change_password(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = data.get("user_id"); current_password = data.get("current_password"); new_password = data.get("new_password")
        if not user_id: raise HTTPException(status_code=400, detail="User ID required")
        user = db.query(User).filter(User.id == user_id).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(current_password, user.password): raise HTTPException(status_code=400, detail="Current password incorrect")
        if not validate_password(new_password): raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        user.password = hash_password(new_password); db.commit()
        return {"message": "Password changed successfully"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))