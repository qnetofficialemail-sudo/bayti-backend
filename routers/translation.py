from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_seller, get_current_user
from models.user import Product, SellerProfile
from services.translation import translate_product_to_arabic
from pydantic import BaseModel

router = APIRouter(prefix="/api/translate", tags=["translation"])

class TranslateRequest(BaseModel):
    name: str
    description: str
    category: str = None

@router.post("/arabic")
def translate_to_arabic(data: TranslateRequest, current_user=Depends(get_current_user)):
    """Translate product name and description to Arabic."""
    result = translate_product_to_arabic(data.name, data.description, data.category)
    return result

@router.post("/product/{product_id}")
def translate_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_seller)):
    """Translate an existing product to Arabic and save it."""
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != seller.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    result = translate_product_to_arabic(product.name, product.description or product.name)
    if result["success"]:
        product.name_ar = result["name_ar"]
        product.description_ar = result["description_ar"]
        db.commit()
        return {"success": True, "name_ar": product.name_ar, "description_ar": product.description_ar}
    raise HTTPException(status_code=500, detail="Translation failed")

@router.post("/translate-all-products")
def translate_all_products(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Translate all products that dont have Arabic content yet."""
    products = db.query(Product).filter(Product.name_ar == None).all()
    translated = 0
    for product in products:
        result = translate_product_to_arabic(product.name, product.description or product.name)
        if result["success"]:
            product.name_ar = result["name_ar"]
            product.description_ar = result["description_ar"]
            translated += 1
    db.commit()
    return {"translated": translated, "total": len(products)}
