path = r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\sellers.py'
content = open(path, encoding='utf-8').read()

old = '''@router.patch("/schedule", response_model=SellerProfileOut)
def update_schedule(
    data: SellerScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    if data.available_days is not None:
        seller.available_days = data.available_days
    if data.available_from is not None:
        seller.available_from = data.available_from
    if data.available_until is not None:
        seller.available_until = data.available_until
    if data.accepting_orders is not None:
        seller.accepting_orders = data.accepting_orders

    db.commit()
    db.refresh(seller)
    return seller'''

new = '''@router.patch("/schedule", response_model=SellerProfileOut)
def update_schedule(
    data: SellerScheduleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    # Use model_fields_set to detect explicitly passed fields (including null)
    fields = data.model_dump(exclude_unset=False)
    seller.available_days = fields.get("available_days")
    seller.available_from = fields.get("available_from")
    seller.available_until = fields.get("available_until")
    if data.accepting_orders is not None:
        seller.accepting_orders = data.accepting_orders

    db.commit()
    db.refresh(seller)
    return seller'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Schedule endpoint fixed - now properly clears null values")
else:
    print("❌ Pattern not found")
