# Builds password reset feature for Bayti
# 1. Backend: forgot-password + reset-password endpoints in auth.py
# 2. Frontend: ForgotPasswordPage + ResetPasswordPage + link in LoginPage

BACKEND_CODE = '''
# ── Add to routers/auth.py ─────────────────────────────────────────────
# Add these imports at the top of auth.py:
# import secrets, datetime
# from services.email_service import send_email

# ── In-memory token store (add as module-level variable) ───────────────
# password_reset_tokens = {}  # {token: {user_id, expires_at}}

# ── Add these 3 endpoints ──────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    from models.user import User
    import secrets, datetime
    from services.email_service import send_email
    
    email = data.get("email", "").lower().strip()
    user = db.query(User).filter(User.email == email).first()
    
    # Always return success (don't reveal if email exists)
    if not user:
        return {"message": "If this email exists, a reset link has been sent."}
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    
    # Store token (module level dict)
    import routers.auth as auth_module
    auth_module.password_reset_tokens[token] = {
        "user_id": user.id,
        "expires_at": expires
    }
    
    # Send email
    reset_url = f"https://bayti.ink/reset-password?token={token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #FF5A1F; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🏠 Bayti بيتي</h1>
      </div>
      <div style="background: #fff7ed; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #fed7aa;">
        <h2 style="color: #1f2937;">Reset Your Password</h2>
        <p style="color: #4b5563;">Hi {user.full_name},</p>
        <p style="color: #4b5563;">We received a request to reset your password. Click the button below to create a new password:</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{reset_url}" style="background: #FF5A1F; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
            Reset Password
          </a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">This link expires in 30 minutes.</p>
        <p style="color: #6b7280; font-size: 14px;">If you did not request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #fed7aa; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; text-align: center;">
          Or copy this link: {reset_url}
        </p>
      </div>
    </div>
    """
    send_email(user.email, "Reset Your Bayti Password", html)
    return {"message": "If this email exists, a reset link has been sent."}


@router.post("/verify-reset-token")
def verify_reset_token(data: dict):
    import datetime, routers.auth as auth_module
    token = data.get("token", "")
    token_data = auth_module.password_reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if datetime.datetime.utcnow() > token_data["expires_at"]:
        del auth_module.password_reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    return {"valid": True}


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    import datetime, routers.auth as auth_module
    from models.user import User
    from core.auth import hash_password
    
    token = data.get("token", "")
    new_password = data.get("new_password", "")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    token_data = auth_module.password_reset_tokens.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if datetime.datetime.utcnow() > token_data["expires_at"]:
        del auth_module.password_reset_tokens[token]
        raise HTTPException(status_code=400, detail="Token expired")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = hash_password(new_password)
    db.commit()
    
    # Delete used token
    del auth_module.password_reset_tokens[token]
    
    return {"message": "Password reset successfully"}
'''

print("Backend code ready")
print("="*50)

# Now let's patch auth.py
import os
BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
auth_path = os.path.join(BACKEND, "routers", "auth.py")
content = open(auth_path, "rb").read()

# Check what's in auth.py
print(f"auth.py size: {len(content)} bytes")
print("First 200 bytes:", content[:200])
