path = r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\admin.py'
content = open(path, encoding='utf-8').read()

# Fix delete_user to handle sellers by finding their seller profile
old = '''@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    """Permanently delete a user account from the database."""
    from models.user import User, Order, OrderItem
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin accounts")
    if user.role == "seller":
        raise HTTPException(status_code=400, detail="Use delete seller endpoint for seller accounts")
    
    # Delete buyer's order items and orders
    orders = db.query(Order).filter(Order.buyer_id == user_id).all()
    for order in orders:
        db.query(OrderItem).filter(OrderItem.order_id == order.id).delete(synchronize_session=False)
    db.query(Order).filter(Order.buyer_id == user_id).delete(synchronize_session=False)
    
    # Delete user
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}'''

new = '''@router.delete("/users/{user_id}")
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
    return {"message": "User deleted successfully"}'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ delete_user fixed to handle sellers!")
else:
    print("❌ Pattern not found")
