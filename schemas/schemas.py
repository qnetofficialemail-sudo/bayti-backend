from pydantic import BaseModel, EmailStr
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
