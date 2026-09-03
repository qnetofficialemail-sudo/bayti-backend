import os

files = {}

files['routers/products.py'] = '''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from core.auth import get_current_user, get_current_seller
from models.user import Product, SellerProfile, Category
from schemas.schemas import ProductOut
from services.translation import translate_product_to_arabic
import shutil, os, uuid

router = APIRouter(prefix="/api/products", tags=["products"])

UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
def create_product(
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
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_url = f"/uploads/products/{filename}"

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
def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
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
        try:
            result = translate_product_to_arabic(name, description or product.description or name)
            if result["success"]:
                product.name_ar = result["name_ar"]
                product.description_ar = result["description_ar"]
        except Exception as e:
            print(f"Re-translation failed: {e}")
    if description is not None: product.description = description
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
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        product.image_url = f"/uploads/products/{filename}"

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
'''

files['routers/orders.py'] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.auth import get_current_user, get_current_seller
from models.user import Order, OrderItem, Product, SellerProfile
from schemas.schemas import OrderCreate, OrderOut
from services.whatsapp import notify_seller_new_order

router = APIRouter(prefix="/api/orders", tags=["orders"])

DELIVERY_FEE = 10.0

@router.post("/", response_model=OrderOut)
def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "seller":
        raise HTTPException(status_code=403, detail="Sellers cannot place orders")

    seller = db.query(SellerProfile).filter(SellerProfile.id == data.seller_id).first()
    if not seller or not seller.is_approved:
        raise HTTPException(status_code=404, detail="Seller not found or not approved")

    total = 0.0
    order_items = []
    for item_data in data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.seller_id == seller.id,
            Product.is_available == True
        ).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item_data.product_id} not available")

        # Check stock
        if product.track_stock and product.stock_quantity != -1:
            if product.stock_quantity < item_data.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for {product.name}. Only {product.stock_quantity} left."
                )

        subtotal = product.price * item_data.quantity
        total += subtotal
        order_items.append((OrderItem(
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=product.price,
        ), product, item_data.quantity))

    order = Order(
        buyer_id=current_user.id,
        seller_id=seller.id,
        delivery_address=data.delivery_address,
        delivery_area=data.delivery_area,
        notes=data.notes,
        total_amount=total,
        delivery_fee=DELIVERY_FEE,
        status="pending",
    )
    db.add(order)
    db.flush()

    items_for_notification = []
    for item, product, quantity in order_items:
        item.order_id = order.id
        db.add(item)

        # Deduct stock
        if product.track_stock and product.stock_quantity != -1:
            product.stock_quantity -= quantity
            if product.stock_quantity <= 0:
                product.stock_quantity = 0
                product.is_available = False
                print(f"Product {product.name} is now out of stock")

        items_for_notification.append({"quantity": quantity, "name": product.name})

    seller.total_orders += 1
    db.commit()
    db.refresh(order)

    try:
        if seller.user.phone:
            notify_seller_new_order(
                seller_phone=seller.user.phone,
                seller_name=seller.shop_name,
                buyer_name=current_user.full_name,
                items=items_for_notification,
                total=order.total_amount + order.delivery_fee,
                area=order.delivery_area,
                notes=order.notes
            )
    except Exception as e:
        print(f"WhatsApp notification failed: {e}")

    return order

@router.get("/my", response_model=List[OrderOut])
def my_orders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role in ("seller", "admin"):
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if seller:
            return db.query(Order).filter(Order.seller_id == seller.id).order_by(Order.created_at.desc()).all()
        return []
    return db.query(Order).filter(Order.buyer_id == current_user.id).order_by(Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    is_owner = order.buyer_id == current_user.id
    is_seller = seller and order.seller_id == seller.id
    if not (is_owner or is_seller or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    return order

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    valid_transitions = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["preparing", "cancelled"],
        "preparing": ["ready"],
        "ready": ["delivering"],
        "delivering": ["delivered"],
    }
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    is_seller = seller and order.seller_id == seller.id
    is_buyer = order.buyer_id == current_user.id

    if not (is_seller or is_buyer or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    allowed = valid_transitions.get(order.status, [])
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot move from \'{order.status}\' to \'{status}\'")

    order.status = status
    db.commit()
    return {"order_id": order_id, "status": order.status}
'''

files['models/user.py'] = '''from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum

class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"

class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    delivering = "delivering"
    delivered = "delivered"
    cancelled = "cancelled"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="buyer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="buyer")

class SellerProfile(Base):
    __tablename__ = "seller_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    shop_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    area = Column(String, nullable=False)
    city = Column(String, default="Dubai")
    logo_url = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    name_ar = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String, nullable=False)
    name_ar = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    preparation_time = Column(Integer, default=60)
    stock_quantity = Column(Integer, default=-1)
    track_stock = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    seller = relationship("SellerProfile", back_populates="products")
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"))
    status = Column(String, default="pending")
    delivery_address = Column(Text, nullable=False)
    delivery_area = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=10.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    buyer = relationship("User", back_populates="orders")
    seller = relationship("SellerProfile")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
'''

files['schemas/schemas.py'] = '''from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    password: str
    role: str = "buyer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class SellerProfileCreate(BaseModel):
    shop_name: str
    description: Optional[str] = None
    area: str
    city: str = "Dubai"

class SellerProfileOut(BaseModel):
    id: int
    shop_name: str
    description: Optional[str]
    area: str
    city: str
    logo_url: Optional[str]
    is_approved: bool
    rating: float
    total_orders: int
    user: UserOut
    class Config:
        from_attributes = True

class CategoryOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    icon: Optional[str]
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[int] = None
    preparation_time: int = 60
    is_available: bool = True
    stock_quantity: int = -1
    track_stock: bool = False

class ProductOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str]
    description_ar: Optional[str] = None
    price: float
    image_url: Optional[str]
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    category: Optional[CategoryOut]
    seller: Optional[SellerProfileOut] = None
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    seller_id: int
    delivery_address: str
    delivery_area: str
    notes: Optional[str] = None
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product: Optional[ProductOut]
    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    status: str
    delivery_address: str
    delivery_area: str
    total_amount: float
    delivery_fee: float
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemOut]
    buyer: Optional[UserOut]
    seller: Optional[SellerProfileOut]
    class Config:
        from_attributes = True
'''

for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nBackend inventory files written!")
