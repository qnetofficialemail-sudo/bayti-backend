import os

files = {}

files['routers/admin.py'] = '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from core.database import get_db
from core.auth import get_current_admin
from models.user import User, SellerProfile, Order, Product
from sqlalchemy import func
import shutil, os, uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    total_sellers = db.query(SellerProfile).count()
    pending_sellers = db.query(SellerProfile).filter(SellerProfile.is_approved == False).count()
    approved_sellers = db.query(SellerProfile).filter(SellerProfile.is_approved == True).count()
    total_buyers = db.query(User).filter(User.role == "buyer").count()
    total_orders = db.query(Order).count()
    total_products = db.query(Product).count()
    revenue = db.query(func.sum(Order.total_amount + Order.delivery_fee)).scalar() or 0
    platform_commission = revenue * 0.12
    return {
        "total_sellers": total_sellers,
        "pending_sellers": pending_sellers,
        "approved_sellers": approved_sellers,
        "total_buyers": total_buyers,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_revenue": round(revenue, 2),
        "platform_commission": round(platform_commission, 2),
    }

@router.get("/sellers")
def list_all_sellers(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    query = db.query(SellerProfile)
    if status == "pending":
        query = query.filter(SellerProfile.is_approved == False)
    elif status == "approved":
        query = query.filter(SellerProfile.is_approved == True)
    sellers = query.order_by(SellerProfile.created_at.desc()).all()
    return [{
        "id": s.id,
        "shop_name": s.shop_name,
        "area": s.area,
        "city": s.city,
        "is_approved": s.is_approved,
        "badge": s.badge,
        "badge_notes": s.badge_notes,
        "rating": s.rating,
        "total_orders": s.total_orders,
        "description": s.description,
        "created_at": s.created_at,
        "user": {
            "id": s.user.id,
            "full_name": s.user.full_name,
            "email": s.user.email,
            "phone": s.user.phone,
        }
    } for s in sellers]

@router.patch("/sellers/{seller_id}/approve")
def approve_seller(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = True
    db.commit()
    return {"message": f"{seller.shop_name} approved", "seller_id": seller_id}

@router.patch("/sellers/{seller_id}/reject")
def reject_seller(
    seller_id: int,
    reason: str = "Does not meet requirements",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = False
    seller.badge_notes = f"Rejected: {reason}"
    db.commit()
    return {"message": f"{seller.shop_name} rejected"}

@router.patch("/sellers/{seller_id}/badge")
def update_badge(
    seller_id: int,
    badge: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    valid_badges = ["verified", "inspected", "certified"]
    if badge not in valid_badges and badge != "none":
        raise HTTPException(status_code=400, detail=f"Badge must be one of: {valid_badges}")
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.badge = badge if badge != "none" else None
    if notes:
        seller.badge_notes = notes
    db.commit()
    return {"message": f"Badge updated to {badge}", "seller_id": seller_id}

@router.patch("/sellers/{seller_id}/disable")
def disable_seller(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = False
    for product in seller.products:
        product.is_available = False
    db.commit()
    return {"message": f"{seller.shop_name} disabled and products hidden"}

@router.get("/orders")
def list_all_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    return [{
        "id": o.id,
        "status": o.status,
        "total": round(o.total_amount + o.delivery_fee, 2),
        "area": o.delivery_area,
        "created_at": o.created_at,
        "buyer": o.buyer.full_name if o.buyer else None,
        "seller": o.seller.shop_name if o.seller else None,
        "items_count": len(o.items),
    } for o in orders]

@router.get("/users")
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    return [{
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at,
    } for u in users]

@router.patch("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'enabled' if user.is_active else 'disabled'}", "is_active": user.is_active}
'''

for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nAdmin backend written!")
