from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.auth import get_current_user, get_current_seller
from models.user import Order, OrderItem, Product, SellerProfile
from schemas.schemas import OrderCreate, OrderOut
from services.whatsapp import notify_seller_new_order
from routers.sellers import is_seller_open

router = APIRouter(prefix="/api/orders", tags=["orders"])

DELIVERY_FEE = 10.0

@router.post("/", response_model=OrderOut)
def create_order(data: OrderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "seller":
        raise HTTPException(status_code=403, detail="Sellers cannot place orders")

    seller = db.query(SellerProfile).filter(SellerProfile.id == data.seller_id).first()
    if not seller or not seller.is_approved:
        raise HTTPException(status_code=404, detail="Seller not found or not approved")

    # Check seller schedule
    status = is_seller_open(seller)
    if not status["is_open"]:
        raise HTTPException(status_code=400, detail=f"Seller is not accepting orders right now. {status['message']}")

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
    actual_delivery_fee = data.delivery_fee if data.delivery_fee is not None else DELIVERY_FEE
    order_total = total + actual_delivery_fee
    commission_rate = seller.commission_rate if seller.commission_rate is not None else 12.0
    commission_amount = round(order_total * commission_rate / 100, 2)

    from datetime import datetime, timedelta
    import pytz
    cancel_dl = datetime.now(pytz.UTC) + timedelta(minutes=10)
    order = Order(
        buyer_id=current_user.id,
        seller_id=seller.id,
        delivery_address=data.delivery_address,
        delivery_area=data.delivery_area,
        notes=data.notes,
        buyer_phone=data.buyer_phone,
        total_amount=total,
        delivery_fee=actual_delivery_fee,
        commission_amount=commission_amount,
        status="pending",
        cancel_deadline=cancel_dl,
    )
    db.add(order)
    db.flush()

    items_for_notification = []
    for item, product, quantity in order_items:
        product.sold_count = (product.sold_count or 0) + quantity
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

    # Track response time when seller confirms
    if status == "confirmed" and order.confirmed_at is None:
        from datetime import datetime, timezone as tz
        now = datetime.now(tz.utc)
        order.confirmed_at = now
        if order.created_at:
            created = order.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=tz.utc)
            diff_minutes = (now - created).total_seconds() / 60
            seller_obj = db.query(SellerProfile).filter(SellerProfile.id == order.seller_id).first()
            if seller_obj:
                confirmed_orders = db.query(Order).filter(
                    Order.seller_id == seller_obj.id,
                    Order.confirmed_at != None
                ).order_by(Order.confirmed_at.desc()).limit(19).all()
                times = []
                for co in confirmed_orders:
                    if co.created_at and co.confirmed_at:
                        c = co.created_at
                        cf = co.confirmed_at
                        if c.tzinfo is None:
                            c = c.replace(tzinfo=tz.utc)
                        if cf.tzinfo is None:
                            cf = cf.replace(tzinfo=tz.utc)
                        times.append((cf - c).total_seconds() / 60)
                times.append(diff_minutes)
                seller_obj.avg_response_minutes = round(sum(times) / len(times), 1)

    db.commit()
    return {"order_id": order_id, "status": order.status}


@router.delete("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from datetime import datetime
    import pytz
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending orders")
    now = datetime.now(pytz.UTC)
    if order.cancel_deadline and now > order.cancel_deadline:
        raise HTTPException(status_code=400, detail="Cancellation window has passed (10 minutes)")
    order.status = "cancelled"
    db.commit()
    return {"message": "Order cancelled successfully"}


@router.patch("/{order_id}/reject")
def reject_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_seller)):
    """Seller rejects/cancels an order."""
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    order = db.query(Order).filter(Order.id == order_id, Order.seller_id == seller.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ["delivered", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel a delivered or already cancelled order")
    order.status = "cancelled"
    db.commit()
    return {"message": "Order rejected", "order_id": order_id, "status": "cancelled"}
