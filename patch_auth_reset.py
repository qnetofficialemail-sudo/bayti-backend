import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
auth_path = os.path.join(BACKEND, "routers", "auth.py")

new_content = '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import verify_password, hash_password, create_access_token, get_current_user
from models.user import User
from schemas.schemas import UserRegister, Token
import secrets, datetime

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory token store for password reset
password_reset_tokens = {}

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
def get_me(current_user: User = Depends(get_current_user)):
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

@router.post("/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    from services.email_service import send_email
    email = data.get("email", "").lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If this email exists, a reset link has been sent."}
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    password_reset_tokens[token] = {"user_id": user.id, "expires_at": expires}
    reset_url = f"https://bayti.ink/reset-password?token={token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #FF5A1F; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">&#127968; Bayti &#1576;&#1610;&#1578;&#1610;</h1>
      </div>
      <div style="background: #fff7ed; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #fed7aa;">
        <h2 style="color: #1f2937;">Reset Your Password</h2>
        <p style="color: #4b5563;">Hi {user.full_name},</p>
        <p style="color: #4b5563;">We received a request to reset your password. Click the button below:</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{reset_url}" style="background: #FF5A1F; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">Reset Password</a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">This link expires in 30 minutes.</p>
        <p style="color: #6b7280; font-size: 14px;">If you did not request this, ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #fed7aa; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">Or copy: {reset_url}</p>
      </div>
    </div>
    """
    send_email(user.email, "Reset Your Bayti Password | اعادة تعيين كلمة المرور", html)
    return {"message": "If this email exists, a reset link has been sent."}

@router.post("/verify-reset-token")
def verify_reset_token(data: dict):
    token = data.get("token", "")
    token_data = password_reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if datetime.datetime.utcnow() > token_data["expires_at"]:
        del password_reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    return {"valid": True}

@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    token = data.get("token", "")
    new_password = data.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    token_data = password_reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if datetime.datetime.utcnow() > token_data["expires_at"]:
        del password_reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(new_password)
    db.commit()
    del password_reset_tokens[token]
    return {"message": "Password reset successfully"}
'''

with open(auth_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Done! Size:", len(new_content))
