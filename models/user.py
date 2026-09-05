from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum
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
    saved_address = Column(String, nullable=True)
    saved_area = Column(String, nullable=True)
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
    badge = Column(Text, nullable=True)
    badge_notes = Column(Text, nullable=True)
    license_url = Column(Text, nullable=True)
    kitchen_photo_url = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    commission_rate = Column(Float, default=12.0)
    available_days = Column(String, nullable=True)
    available_from = Column(String, nullable=True)
    available_until = Column(String, nullable=True)
    accepting_orders = Column(Boolean, default=True)
    # New seller profile fields
    whatsapp_number = Column(String, nullable=True)
    instagram_handle = Column(String, nullable=True)
    min_order_amount = Column(Float, nullable=True)
    delivery_type = Column(String, nullable=True)     # "self" or "bayti"
    categories_offered = Column(String, nullable=True) # comma-separated category ids
    sample_image_1 = Column(String, nullable=True)
    sample_image_2 = Column(String, nullable=True)
    sample_image_3 = Column(String, nullable=True)
    avg_response_minutes = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    name_ar = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
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
    time_unit = Column(String, default="minutes")  # minutes, hours, days
    stock_quantity = Column(Integer, default=-1)
    track_stock = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    sold_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    seller = relationship("SellerProfile", back_populates="products")
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

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
    commission_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    cancel_deadline = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    buyer = relationship("User", back_populates="orders")
    seller = relationship("SellerProfile")
    items = relationship("OrderItem", back_populates="order")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"))
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)  # admin must approve
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("SellerProfile", foreign_keys=[seller_id])
    order = relationship("Order", foreign_keys=[order_id])

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    selected_variants = Column(Text, nullable=True)  # JSON: {"Size":"M","Color":"Black"}
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class SellerApplication(Base):
    __tablename__ = "seller_applications"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    area = Column(String, nullable=False)
    city = Column(String, default="Dubai")
    what_they_sell = Column(Text, nullable=False)
    doc_1_url = Column(Text, nullable=True)
    doc_2_url = Column(Text, nullable=True)
    doc_3_url = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    invite_token = Column(String, nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)        # e.g. "Size", "Color", "Scent"
    name_ar = Column(String, nullable=True)      # Arabic name
    options = Column(Text, nullable=False)       # JSON: [{"label":"S","price_adj":0},{"label":"M","price_adj":5}]
    is_required = Column(Boolean, default=True)
    product = relationship("Product", back_populates="variants")
