from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.auth import get_current_user, get_current_seller
from models.user import SellerProfile
from schemas.schemas import SellerProfileOut, SellerProfileCreate, SellerScheduleUpdate
from datetime import datetime
import pytz

router = APIRouter(prefix="/api/sellers", tags=["sellers"])

def is_seller_open(seller: SellerProfile) -> dict:
    """Check if seller is currently accepting orders based on schedule."""
    if not seller.accepting_orders:
        return {"is_open": False, "reason": "closed", "message": "Not accepting orders today"}

    if not seller.available_days and not seller.available_from:
        return {"is_open": True, "reason": "always_open", "message": ""}

    # Check in UAE time (UTC+4)
    uae_tz = pytz.timezone("Asia/Dubai")
    now = datetime.now(uae_tz)
    weekday = now.weekday()  # 0=Mon, 6=Sun
    current_time = now.strftime("%H:%M")

    # Check day
    if seller.available_days:
        allowed_days = [int(d.strip()) for d in seller.available_days.split(",") if d.strip()]
        if weekday not in allowed_days:
            day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            allowed_names = [day_names[d] for d in sorted(allowed_days)]
            return {"is_open": False, "reason": "wrong_day", "message": f"Available: {', '.join(allowed_names)}"}

    # Check time
    if seller.available_from and seller.available_until:
        if not (seller.available_from <= current_time <= seller.available_until):
            return {"is_open": False, "reason": "outside_hours",
                    "message": f"Opens {seller.available_from} – {seller.available_until}"}

    return {"is_open": True, "reason": "open", "message": ""}

@router.get("/", response_model=List[SellerProfileOut])
def list_sellers(db: Session = Depends(get_db)):
    return db.query(SellerProfile).filter(SellerProfile.is_approved == True).all()

@router.get("/{seller_id}/status")
def seller_status(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return is_seller_open(seller)

@router.get("/{seller_id}/public")
def get_seller_public(seller_id: int, db: Session = Depends(get_db)):
    """Public seller profile - hides contact details."""
    seller = db.query(SellerProfile).filter(
        SellerProfile.id == seller_id,
        SellerProfile.is_approved == True
    ).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {
        "id": seller.id,
        "shop_name": seller.shop_name,
        "description": seller.description,
        "area": seller.area,
        "city": seller.city,
        "logo_url": seller.logo_url,
        "badge": seller.badge,
        "rating": seller.rating,
        "total_orders": seller.total_orders,
        "categories_offered": seller.categories_offered,
        "sample_image_1": seller.sample_image_1,
        "sample_image_2": seller.sample_image_2,
        "sample_image_3": seller.sample_image_3,
        "min_order_amount": seller.min_order_amount,
        "delivery_type": seller.delivery_type,
        "available_from": seller.available_from,
        "available_until": seller.available_until,
        "available_days": seller.available_days,
        "accepting_orders": seller.accepting_orders,
    }


@router.patch("/profile/edit")
async def edit_seller_profile(
    shop_name: Optional[str] = None,
    description: Optional[str] = None,
    area: Optional[str] = None,
    city: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    instagram_handle: Optional[str] = None,
    min_order_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    if shop_name is not None: seller.shop_name = shop_name
    if description is not None: seller.description = description
    if area is not None: seller.area = area
    if city is not None: seller.city = city
    if whatsapp_number is not None: seller.whatsapp_number = whatsapp_number
    if instagram_handle is not None: seller.instagram_handle = instagram_handle
    if min_order_amount is not None: seller.min_order_amount = min_order_amount
    db.commit()
    db.refresh(seller)
    return seller

@router.patch("/schedule", response_model=SellerProfileOut)
def update_schedule(
    data: SellerScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    # Use model_fields_set to detect explicitly passed fields (including null)
    fields = data.model_dump(exclude_unset=False)
    seller.available_days = fields.get("available_days")
    seller.available_from = fields.get("available_from")
    seller.available_until = fields.get("available_until")
    if data.accepting_orders is not None:
        seller.accepting_orders = data.accepting_orders

    db.commit()
    db.refresh(seller)
    return seller

@router.post("/", response_model=SellerProfileOut)
def create_seller_profile(
    data: SellerProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")
    seller = SellerProfile(
        user_id=current_user.id,
        shop_name=data.shop_name,
        description=data.description,
        area=data.area,
        city=data.city,
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller

@router.post("/profile", response_model=SellerProfileOut)
async def create_seller_profile_form(
    shop_name: str = Form(...),
    description: Optional[str] = Form(None),
    area: str = Form(...),
    city: str = Form("Dubai"),
    whatsapp_number: Optional[str] = Form(None),
    instagram_handle: Optional[str] = Form(None),
    min_order_amount: Optional[float] = Form(None),
    delivery_type: Optional[str] = Form("bayti"),
    categories_offered: Optional[str] = Form(None),
    sample_image_1: Optional[UploadFile] = File(None),
    sample_image_2: Optional[UploadFile] = File(None),
    sample_image_3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Form-based seller profile creation (used by SellerSetup page)."""
    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")

    # Upload sample images to Cloudinary
    from services.cloudinary_upload import upload_seller_logo
    import uuid

    def upload_sample(img):
        if not img:
            return None
        try:
            data = img.file.read()
            ext = img.filename.split(".")[-1]
            return upload_seller_logo(data, f"sample_{uuid.uuid4()}.{ext}")
        except:
            return None

    seller = SellerProfile(
        user_id=current_user.id,
        shop_name=shop_name,
        description=description,
        area=area,
        city=city,
        accepting_orders=True,
        whatsapp_number=whatsapp_number,
        instagram_handle=instagram_handle,
        min_order_amount=min_order_amount,
        delivery_type=delivery_type,
        categories_offered=categories_offered,
        sample_image_1=upload_sample(sample_image_1),
        sample_image_2=upload_sample(sample_image_2),
        sample_image_3=upload_sample(sample_image_3),
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller
