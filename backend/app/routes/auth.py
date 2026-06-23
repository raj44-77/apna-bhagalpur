from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import bcrypt, re, random, json
from ..database import get_db
from ..models.user import User
from ..models.clinic import Clinic
from ..models.verification_code import VerificationCode

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()

from ..config import get_settings
settings = get_settings()
SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


class LoginData(BaseModel):
    email: str
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
    if not phone.isdigit() or len(phone) != 10: return False
    if phone[0] not in '6789': return False
    spam = ['1111111111','2222222222','3333333333','4444444444','5555555555','6666666666','7777777777','8888888888','9999999999','0000000000','1234567890','0987654321','1122334455','1234512345','9876598765','9000000000']
    if phone in spam: return False
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


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        user_type = payload.get("type")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "user_type": user_type}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_clinic_admin(user: dict = Depends(get_current_user)):
    if user["user_type"] not in ["clinic", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied. Clinic admin only.")
    return user


def require_clinic_owner(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the clinic_id that this user owns. Super admin bypasses check."""
    if user["user_type"] == "admin":
        return None
    
    user_record = db.query(User).filter(User.id == user["user_id"]).first()
    if not user_record or not user_record.clinic_id:
        raise HTTPException(status_code=403, detail="No clinic associated with your account.")
    
    return user_record.clinic_id


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginData, db: Session = Depends(get_db)):
    try:
        login_value = data.email.strip().lower()
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
            "user": {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone, "user_type": user.user_type, "clinic_id": user.clinic_id, "clinic_name": clinic_name, "age": user.age, "gender": user.gender, "is_active": bool(user.is_active), "created_at": str(user.created_at)}
        }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/google-login")
@limiter.limit("10/minute")
async def google_login(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email")
        name = data.get("name", "Google User")
        google_id = data.get("google_id", "")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=name, email=email, phone=f"gg{google_id[:8]}", password=hash_password(google_id), user_type="patient")
            db.add(user); db.commit(); db.refresh(user)
        access_token = create_access_token(user.id, user.user_type)
        return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone, "user_type": user.user_type, "clinic_id": user.clinic_id, "clinic_name": None, "age": user.age, "gender": user.gender, "is_active": bool(user.is_active), "created_at": str(user.created_at)}}
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
        if not validate_name(name): raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        if not validate_password(password): raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        if is_email(login_value):
            if not validate_email(login_value): raise HTTPException(status_code=400, detail="Invalid email format")
            email = login_value.lower()
            if db.query(User).filter(User.email == email).first(): raise HTTPException(status_code=400, detail="Email already registered")
            code = str(random.randint(100000, 999999))
            user_data = json.dumps({"name": name, "password": hash_password(password), "age": int(age) if age and str(age).isdigit() else None, "gender": gender})
            vcode = VerificationCode(email=email, code=code, code_type="email_verify", user_data=user_data, expires_at=datetime.utcnow() + timedelta(minutes=10))
            db.add(vcode); db.commit()
            return {"message": "Verification code sent", "code": code, "email": email, "step": "verify_email"}
        elif is_phone(login_value):
            if not is_valid_indian_mobile(login_value): raise HTTPException(status_code=400, detail="Invalid phone number")
            if db.query(User).filter(User.phone == login_value).first(): raise HTTPException(status_code=400, detail="Phone already registered")
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
        vcode = db.query(VerificationCode).filter(VerificationCode.email == email, VerificationCode.code == code, VerificationCode.code_type == "email_verify", VerificationCode.expires_at > datetime.utcnow()).first()
        if not vcode: raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        user_data = json.loads(vcode.user_data)
        user = User(name=user_data["name"], email=email, phone=f"em{random.randint(100000,999999)}", password=user_data["password"], user_type="patient", age=user_data.get("age"), gender=user_data.get("gender"))
        db.add(user); db.delete(vcode); db.commit(); db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email, "message": "Email verified! Account created."}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/register/clinic")
@limiter.limit("3/hour")
async def register_clinic(request: Request, data: dict, db: Session = Depends(get_db)):
    try:
        if not validate_name(data.get("name", "")): raise HTTPException(status_code=400, detail="Name must be at least 3 characters")
        if not validate_email(data.get("email", "")): raise HTTPException(status_code=400, detail="Invalid email format")
        if not validate_phone(data.get("phone", "")): raise HTTPException(status_code=400, detail="Phone must be exactly 10 digits")
        if not validate_password(data.get("password", "")): raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        if db.query(User).filter(User.email == data["email"]).first(): raise HTTPException(status_code=400, detail="Email already registered")
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
        db.query(VerificationCode).filter(VerificationCode.email == email, VerificationCode.code_type == "password_reset").delete()
        vcode = VerificationCode(email=email, code=reset_code, code_type="password_reset", user_data=str(user.id), expires_at=datetime.utcnow() + timedelta(minutes=10))
        db.add(vcode); db.commit()
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
        vcode = db.query(VerificationCode).filter(VerificationCode.email == email, VerificationCode.code == code, VerificationCode.code_type == "password_reset", VerificationCode.expires_at > datetime.utcnow()).first()
        if not vcode: raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        user_id = int(vcode.user_data)
        user = db.query(User).filter(User.id == user_id).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        user.password = hash_password(new_password)
        db.delete(vcode); db.commit()
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
        e = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if e: raise HTTPException(status_code=400, detail="Email already in use")
        p = db.query(User).filter(User.phone == data["phone"], User.id != user_id).first()
        if p: raise HTTPException(status_code=400, detail="Phone already in use")
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
        user_id = data.get("user_id"); cp = data.get("current_password"); np = data.get("new_password")
        if not user_id: raise HTTPException(status_code=400, detail="User ID required")
        user = db.query(User).filter(User.id == user_id).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(cp, user.password): raise HTTPException(status_code=400, detail="Current password incorrect")
        if not validate_password(np): raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        user.password = hash_password(np); db.commit()
        return {"message": "Password changed successfully"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))