from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
from core.auth import get_current_seller
from services.ai_service import generate_product_description, suggest_price
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import Product

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/generate-description")
async def generate_description(
    product_name: str = Form(...),
    category: str = Form(None),
    price: float = Form(None),
    language: str = Form("en"),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_seller)
):
    image_data = None
    image_type = "image/jpeg"
    if image:
        image_data = await image.read()
        image_type = image.content_type or "image/jpeg"

    result = generate_product_description(
        product_name=product_name,
        category=category,
        price=price,
        image_data=image_data,
        image_type=image_type,
        language=language
    )
    return result

@router.post("/suggest-price")
async def suggest_price_endpoint(
    product_name: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    similar = db.query(Product).filter(Product.is_available == True).order_by(Product.created_at.desc()).limit(10).all()
    similar_list = [{"name": p.name, "price": p.price} for p in similar]
    result = suggest_price(product_name, category, similar_list)
    return result
