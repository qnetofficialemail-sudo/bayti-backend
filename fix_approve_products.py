path = r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\admin.py'
content = open(path, encoding='utf-8').read()

old = '''@router.patch("/sellers/{seller_id}/approve")
def approve_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = True
    db.commit()
    return {"message": f"{seller.shop_name} approved"}'''

new = '''@router.patch("/sellers/{seller_id}/approve")
def approve_seller(seller_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_approved = True
    # Re-enable all products when seller is approved/re-enabled
    for product in seller.products:
        product.is_available = True
    db.commit()
    return {"message": f"{seller.shop_name} approved"}'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ approve_seller now re-enables all products")
else:
    print("❌ Pattern not found")
