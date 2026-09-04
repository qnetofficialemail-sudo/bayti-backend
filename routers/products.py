from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.auth import get_current_user, get_current_seller
from models.user import Product, SellerProfile, Category
from schemas.schemas import ProductOut
from services.translation import translate_product_to_arabic
from services.cloudinary_upload import upload_product_image
import uuid

router = APIRouter(prefix="/api/products", tags=["products"])

@router.get("/", response_model=List[ProductOut])
def list_products(
    category_id: Optional[int] = None,
    area: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).join(SellerProfile).filter(
        Product.is_available == True,
        SellerProfile.is_approved == True
    )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if area:
        query = query.filter(SellerProfile.area.ilike(f"%{area}%"))
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.order_by(Product.created_at.desc()).all()

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductOut)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    category_id: Optional[int] = Form(None),
    preparation_time: int = Form(60),
    stock_quantity: int = Form(-1),
    track_stock: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found.")

    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        image_url = upload_product_image(file_bytes, filename)

    product = Product(
        seller_id=seller.id,
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        preparation_time=preparation_time,
        image_url=image_url,
        stock_quantity=stock_quantity if track_stock else -1,
        track_stock=1 if track_stock else 0,
        is_available=True,
    )
    db.add(product)
    db.flush()

    try:
        category_name = None
        if category_id:
            cat = db.query(Category).filter(Category.id == category_id).first()
            if cat:
                category_name = cat.name
        result = translate_product_to_arabic(name, description or name, category_name)
        if result["success"]:
            product.name_ar = result["name_ar"]
            product.description_ar = result["description_ar"]
    except Exception as e:
        print(f"Auto-translation failed: {e}")

    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    name_ar: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    description_ar: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    is_available: Optional[bool] = Form(None),
    preparation_time: Optional[int] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    track_stock: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if name:
        product.name = name
        # Only auto-translate if no manual Arabic provided
        if not name_ar:
            try:
                result = translate_product_to_arabic(name, description or product.description or name)
                if result["success"]:
                    product.name_ar = result["name_ar"]
                    product.description_ar = result["description_ar"]
            except Exception as e:
                print(f"Re-translation failed: {e}")
    if name_ar is not None: product.name_ar = name_ar
    if description is not None: product.description = description
    if description_ar is not None: product.description_ar = description_ar
    if price is not None: product.price = price
    if is_available is not None: product.is_available = is_available
    if preparation_time is not None: product.preparation_time = preparation_time
    if track_stock is not None: product.track_stock = 1 if track_stock else 0
    if stock_quantity is not None: product.stock_quantity = stock_quantity

    # Auto-disable if stock tracking on and quantity is 0
    if product.track_stock and product.stock_quantity == 0:
        product.is_available = False

    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)

    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}/restock")
def restock_product(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    """Quick restock endpoint — add quantity to current stock."""
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock_quantity == -1:
        product.stock_quantity = quantity
        product.track_stock = 1
    else:
        product.stock_quantity += quantity
    product.is_available = True
    db.commit()
    return {"product_id": product_id, "new_stock": product.stock_quantity}

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_seller)):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
