import os

files = {}

files['routers/admin.py'] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.auth import get_current_admin
from models.user import User, SellerProfile, Order, Product
from sqlalchemy import func

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    total_sellers = db.query(SellerProfile).count()
    pending_sellers = db.query(SellerProfile).filter(SellerProfile.is_approved == False).count()
    approved_sellers = db.query(SellerProfile).filter(SellerProfile.is_approved == True).count()
    total_buyers = db.query(User).filter(User.role == "buyer").count()
    total_orders = db.query(Order).count()
    total_products = db.query(Product).count()
    total_revenue = db.query(func.sum(Order.total_amount + Order.delivery_fee)).scalar() or 0
    total_commission = db.query(func.sum(Order.commission_amount)).scalar() or 0
    return {
        "total_sellers": total_sellers,
        "pending_sellers": pending_sellers,
        "approved_sellers": approved_sellers,
        "total_buyers": total_buyers,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_revenue": round(total_revenue, 2),
        "platform_commission": round(total_commission, 2),
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

    result = []
    for s in sellers:
        total_rev = db.query(func.sum(Order.total_amount + Order.delivery_fee)).filter(Order.seller_id == s.id).scalar() or 0
        total_comm = db.query(func.sum(Order.commission_amount)).filter(Order.seller_id == s.id).scalar() or 0
        result.append({
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
            "commission_rate": s.commission_rate,
            "total_revenue": round(total_rev, 2),
            "total_commission": round(total_comm, 2),
            "created_at": s.created_at,
            "user": {
                "id": s.user.id,
                "full_name": s.user.full_name,
                "email": s.user.email,
                "phone": s.user.phone,
            }
        })
    return result

@router.patch("/sellers/{seller_id}/approve")
def approve_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = True
    db.commit()
    return {"message": f"{seller.shop_name} approved"}

@router.patch("/sellers/{seller_id}/reject")
def reject_seller(seller_id: int, reason: str = "Does not meet requirements", db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = False
    seller.badge_notes = f"Rejected: {reason}"
    db.commit()
    return {"message": f"{seller.shop_name} rejected"}

@router.patch("/sellers/{seller_id}/badge")
def update_badge(seller_id: int, badge: str, notes: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
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
    return {"message": f"Badge updated to {badge}"}

@router.patch("/sellers/{seller_id}/commission")
def update_commission(
    seller_id: int,
    rate: float,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    """Set custom commission rate for a seller (0-50%)."""
    if rate < 0 or rate > 50:
        raise HTTPException(status_code=400, detail="Commission rate must be between 0 and 50")
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    old_rate = seller.commission_rate
    seller.commission_rate = rate
    db.commit()
    return {
        "message": f"Commission updated for {seller.shop_name}",
        "old_rate": old_rate,
        "new_rate": rate,
        "seller_id": seller_id
    }

@router.patch("/sellers/{seller_id}/disable")
def disable_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = False
    for product in seller.products:
        product.is_available = False
    db.commit()
    return {"message": f"{seller.shop_name} disabled"}

@router.get("/orders")
def list_all_orders(status: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).limit(100).all()
    return [{
        "id": o.id,
        "status": o.status,
        "total": round(o.total_amount + o.delivery_fee, 2),
        "commission_amount": round(o.commission_amount, 2),
        "commission_rate": round(o.commission_amount / (o.total_amount + o.delivery_fee) * 100, 1) if o.total_amount > 0 else 0,
        "area": o.delivery_area,
        "created_at": o.created_at,
        "buyer": o.buyer.full_name if o.buyer else None,
        "seller": o.seller.shop_name if o.seller else None,
        "items_count": len(o.items),
    } for o in orders]

@router.get("/users")
def list_users(role: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
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
def toggle_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User toggled", "is_active": user.is_active}

@router.get("/commission/summary")
def commission_summary(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Get commission breakdown per seller."""
    sellers = db.query(SellerProfile).filter(SellerProfile.is_approved == True).all()
    result = []
    for s in sellers:
        orders = db.query(Order).filter(Order.seller_id == s.id).all()
        total_rev = sum(o.total_amount + o.delivery_fee for o in orders)
        total_comm = sum(o.commission_amount for o in orders)
        result.append({
            "shop_name": s.shop_name,
            "commission_rate": s.commission_rate,
            "total_orders": len(orders),
            "total_revenue": round(total_rev, 2),
            "total_commission": round(total_comm, 2),
        })
    return sorted(result, key=lambda x: x["total_commission"], reverse=True)
'''

# Update orders router to calculate commission on order creation
files['routers/orders.py'] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.auth import get_current_user
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

    # Calculate commission using seller's custom rate
    order_total = total + DELIVERY_FEE
    commission_rate = seller.commission_rate if seller.commission_rate is not None else 12.0
    commission_amount = round(order_total * commission_rate / 100, 2)

    order = Order(
        buyer_id=current_user.id,
        seller_id=seller.id,
        delivery_address=data.delivery_address,
        delivery_area=data.delivery_area,
        notes=data.notes,
        total_amount=total,
        delivery_fee=DELIVERY_FEE,
        commission_amount=commission_amount,
        status="pending",
    )
    db.add(order)
    db.flush()

    items_for_notification = []
    for item, product, quantity in order_items:
        item.order_id = order.id
        db.add(item)

        if product.track_stock and product.stock_quantity != -1:
            product.stock_quantity -= quantity
            if product.stock_quantity <= 0:
                product.stock_quantity = 0
                product.is_available = False

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
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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
        raise HTTPException(status_code=400, detail=f"Cannot move from {order.status} to {status}")
    order.status = status
    db.commit()
    return {"order_id": order_id, "status": order.status}
'''

# Update models to include new columns
files['update_models_commission.py'] = '''import sys
sys.path.insert(0, '.')

content = open("models/user.py", encoding="utf-8").read()

# Add commission_rate to SellerProfile
if "commission_rate" not in content:
    content = content.replace(
        "    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    user = relationship",
        "    commission_rate = Column(Float, default=12.0)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    user = relationship"
    )
    print("Added commission_rate to SellerProfile")

# Add commission_amount to Order
if "commission_amount" not in content:
    content = content.replace(
        "    notes = Column(Text, nullable=True)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    updated_at",
        "    notes = Column(Text, nullable=True)\n    commission_amount = Column(Float, default=0.0)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())\n    updated_at"
    )
    print("Added commission_amount to Order")

open("models/user.py", "w", encoding="utf-8").write(content)
print("Models updated successfully")
'''

for path, content in files.items():
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

print("\nCommission system written!")
