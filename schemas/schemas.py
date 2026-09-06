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
    delivery_fees: Optional[str] = None
    total_orders: int
    available_days: Optional[str] = None
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    accepting_orders: bool = True
    whatsapp_number: Optional[str] = None
    instagram_handle: Optional[str] = None
    min_order_amount: Optional[float] = None
    delivery_type: Optional[str] = None
    categories_offered: Optional[str] = None
    sample_image_1: Optional[str] = None
    sample_image_2: Optional[str] = None
    sample_image_3: Optional[str] = None
    user: UserOut
    class Config:
        from_attributes = True

class SellerScheduleUpdate(BaseModel):
    available_days: Optional[str] = None
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    accepting_orders: Optional[bool] = None

class CategoryOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
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
    image_url: Optional[str] = None
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    image_5: Optional[str] = None
    primary_image_index: int = 0
    time_unit: Optional[str] = "minutes"
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    is_featured: bool = False
    sold_count: int = 0
    created_at: Optional[datetime] = None
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
    delivery_fee: Optional[float] = None
    buyer_phone: Optional[str] = None

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
    buyer_phone: Optional[str] = None
    created_at: datetime
    items: List[OrderItemOut]
    buyer: Optional[UserOut]
    seller: Optional[SellerProfileOut]
    class Config:
        from_attributes = True
