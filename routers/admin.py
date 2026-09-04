from fastapi import APIRouter, Depends, HTTPException
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
            "whatsapp_number": s.whatsapp_number,
            "instagram_handle": s.instagram_handle,
            "min_order_amount": s.min_order_amount,
            "delivery_type": s.delivery_type,
            "categories_offered": s.categories_offered,
            "sample_image_1": s.sample_image_1,
            "sample_image_2": s.sample_image_2,
            "sample_image_3": s.sample_image_3,
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
    # Re-enable all products when seller is approved/re-enabled
    for product in seller.products:
        product.is_available = True
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


@router.delete("/sellers/{seller_id}")
def delete_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Permanently delete a seller and all their products from the database."""
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Delete all order items linked to seller's products
    from models.user import OrderItem, Order
    product_ids = [p.id for p in seller.products]
    if product_ids:
        db.query(OrderItem).filter(OrderItem.product_id.in_(product_ids)).delete(synchronize_session=False)
    
    # Delete seller's orders
    db.query(Order).filter(Order.seller_id == seller_id).delete(synchronize_session=False)
    
    # Delete seller's products
    from models.user import Product
    db.query(Product).filter(Product.seller_id == seller_id).delete(synchronize_session=False)
    
    # Get user_id before deleting seller
    user_id = seller.user_id
    
    # Delete seller profile
    db.delete(seller)
    db.flush()
    
    # Delete the user account
    from models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
    
    db.commit()
    return {"message": f"Seller and all associated data deleted successfully"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Permanently delete a user account from the database."""
    from models.user import User, Order, OrderItem, Product
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin accounts")
    
    if user.role == "seller":
        # Find and delete seller profile + products
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == user_id).first()
        if seller:
            product_ids = [p.id for p in seller.products]
            if product_ids:
                db.query(OrderItem).filter(OrderItem.product_id.in_(product_ids)).delete(synchronize_session=False)
            db.query(Order).filter(Order.seller_id == seller.id).delete(synchronize_session=False)
            db.query(Product).filter(Product.seller_id == seller.id).delete(synchronize_session=False)
            db.delete(seller)
            db.flush()
    else:
        # Delete buyer orders
        orders = db.query(Order).filter(Order.buyer_id == user_id).all()
        for order in orders:
            db.query(OrderItem).filter(OrderItem.order_id == order.id).delete(synchronize_session=False)
        db.query(Order).filter(Order.buyer_id == user_id).delete(synchronize_session=False)
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# ── Product Moderation ──
@router.get("/products")
def list_all_products(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [{
        "id": p.id,
        "name": p.name,
        "name_ar": p.name_ar,
        "price": p.price,
        "is_available": p.is_available,
        "image_url": p.image_url,
        "seller_id": p.seller_id,
        "shop_name": p.seller.shop_name if p.seller else None,
        "category": p.category.name if p.category else None,
        "created_at": p.created_at,
    } for p in products]

@router.patch("/products/{product_id}/toggle")
def toggle_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_available = not product.is_available
    db.commit()
    return {"id": product_id, "is_available": product.is_available}

@router.delete("/products/{product_id}")
def delete_product_admin(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    from models.user import OrderItem
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.query(OrderItem).filter(OrderItem.product_id == product_id).delete(synchronize_session=False)
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

# ── CSV Export ──
@router.get("/export/sellers")
def export_sellers(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    from fastapi.responses import StreamingResponse
    import csv, io
    sellers = db.query(SellerProfile).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Shop Name","Owner","Email","Phone","Area","City","Status","Rating","Orders","Commission","WhatsApp","Instagram","Min Order","Delivery"])
    for s in sellers:
        writer.writerow([s.id, s.shop_name, s.user.full_name, s.user.email, s.user.phone,
            s.area, s.city, "Approved" if s.is_approved else "Pending",
            s.rating, s.total_orders, f"{s.commission_rate}%",
            s.whatsapp_number or "", s.instagram_handle or "",
            s.min_order_amount or "", s.delivery_type or ""])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bayti_sellers.csv"})

@router.get("/export/orders")
def export_orders(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    from fastapi.responses import StreamingResponse
    import csv, io
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Date","Seller","Buyer","Area","Status","Subtotal","Delivery","Total","Commission"])
    for o in orders:
        writer.writerow([o.id, o.created_at.strftime("%Y-%m-%d %H:%M"),
            o.seller.shop_name if o.seller else "",
            o.buyer.full_name if o.buyer else "",
            o.delivery_area, o.status,
            o.total_amount, o.delivery_fee,
            round(o.total_amount + o.delivery_fee, 2),
            o.commission_amount])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bayti_orders.csv"})

# ── Revenue Stats for Dashboard ──
@router.get("/revenue/daily")
def daily_revenue(db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    from sqlalchemy import cast, Date
    results = db.execute(
        __import__('sqlalchemy').text("""
            SELECT DATE(created_at) as day,
                   COUNT(*) as orders,
                   SUM(total_amount + delivery_fee) as revenue,
                   SUM(commission_amount) as commission
            FROM orders
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
            LIMIT 30
        """)
    ).fetchall()
    return [{"day": str(r[0]), "orders": r[1], "revenue": round(float(r[2] or 0), 2), "commission": round(float(r[3] or 0), 2)} for r in results]


# ── Cook of the Week ──
@router.get("/cook-of-week")
def get_cook_of_week(db: Session = Depends(get_db)):
    """Returns the top performing approved seller based on rating + recent orders."""
    from sqlalchemy import desc
    sellers = db.query(SellerProfile).filter(
        SellerProfile.is_approved == True,
        SellerProfile.rating > 0,
    ).order_by(desc(SellerProfile.rating), desc(SellerProfile.total_orders)).all()
    
    if not sellers:
        return None
    
    # Pick based on week number so it changes weekly
    import datetime
    week_num = datetime.datetime.now().isocalendar()[1]
    seller = sellers[week_num % len(sellers)]
    
    # Get their best product (highest price = premium)
    best_product = db.query(Product).filter(
        Product.seller_id == seller.id,
        Product.is_available == True
    ).order_by(desc(Product.price)).first()
    
    return {
        "id": seller.id,
        "shop_name": seller.shop_name,
        "description": seller.description,
        "area": seller.area,
        "city": seller.city,
        "rating": seller.rating,
        "total_orders": seller.total_orders,
        "badge": seller.badge,
        "sample_image_1": seller.sample_image_1,
        "sample_image_2": seller.sample_image_2,
        "whatsapp_number": seller.whatsapp_number,
        "instagram_handle": seller.instagram_handle,
        "best_product": {
            "id": best_product.id,
            "name": best_product.name,
            "name_ar": best_product.name_ar,
            "price": best_product.price,
            "image_url": best_product.image_url,
            "description": best_product.description,
        } if best_product else None,
    }
