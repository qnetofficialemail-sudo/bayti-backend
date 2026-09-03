from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.auth import get_current_user, get_current_admin
from models.user import SellerProfile, User
from schemas.schemas import SellerProfileCreate, SellerProfileOut
import shutil, os, uuid

router = APIRouter(prefix="/api/sellers", tags=["sellers"])

UPLOAD_DIR = "uploads/logos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[SellerProfileOut])
def list_sellers(area: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(SellerProfile).filter(SellerProfile.is_approved == True)
    if area:
        query = query.filter(SellerProfile.area.ilike(f"%{area}%"))
    return query.order_by(SellerProfile.rating.desc()).all()

@router.get("/{seller_id}", response_model=SellerProfileOut)
def get_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller

@router.post("/profile", response_model=SellerProfileOut)
def create_seller_profile(
    shop_name: str = Form(...),
    description: Optional[str] = Form(None),
    area: str = Form(...),
    city: str = Form("Dubai"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role not in ("seller", "admin"):
        raise HTTPException(status_code=403, detail="Only sellers can create a profile")

    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")

    logo_url = None
    if logo:
        ext = logo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(logo.file, f)
        logo_url = f"/uploads/logos/{filename}"

    profile = SellerProfile(
        user_id=current_user.id,
        shop_name=shop_name,
        description=description,
        area=area,
        city=city,
        logo_url=logo_url,
        is_approved=False,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.patch("/{seller_id}/approve")
def approve_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = True
    db.commit()
    return {"message": f"{seller.shop_name} approved"}
