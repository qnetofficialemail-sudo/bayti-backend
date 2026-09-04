from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import verify_password, hash_password, create_access_token, get_current_user
from models.user import User
from schemas.schemas import UserRegister, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if data.role not in ("buyer", "seller"):
        raise HTTPException(status_code=400, detail="Role must be buyer or seller")

    user = User(
        email=data.email,
        full_name=data.full_name,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}
    }

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}
    }

@router.get("/me")
def get_me(current_user: User = Depends(__import__('core.auth', fromlist=['get_current_user']).get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "phone": current_user.phone,
    }


@router.get("/me/address")
def get_saved_address(current_user=Depends(get_current_user)):
    return {
        "saved_address": current_user.saved_address,
        "saved_area": current_user.saved_area,
    }

@router.patch("/me/address")
def save_address(
    saved_address: str,
    saved_area: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    current_user.saved_address = saved_address
    current_user.saved_area = saved_area
    db.commit()
    return {"message": "Address saved"}
