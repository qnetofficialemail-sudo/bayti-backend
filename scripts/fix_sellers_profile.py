content = open(r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\sellers.py', encoding='utf-8').read()

# Add /profile endpoint after the existing POST /
old = '''@router.post("/", response_model=SellerProfileOut)
def create_seller_profile(
    data: SellerProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")
    seller = SellerProfile(
        user_id=current_user.id,
        shop_name=data.shop_name,
        description=data.description,
        area=data.area,
        city=data.city,
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller'''

new = '''@router.post("/", response_model=SellerProfileOut)
def create_seller_profile(
    data: SellerProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")
    seller = SellerProfile(
        user_id=current_user.id,
        shop_name=data.shop_name,
        description=data.description,
        area=data.area,
        city=data.city,
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller

@router.post("/profile", response_model=SellerProfileOut)
async def create_seller_profile_form(
    shop_name: str = Form(...),
    description: Optional[str] = Form(None),
    area: str = Form(...),
    city: str = Form("Dubai"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Form-based seller profile creation (used by SellerSetup page)."""
    existing = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Seller profile already exists")
    seller = SellerProfile(
        user_id=current_user.id,
        shop_name=shop_name,
        description=description,
        area=area,
        city=city,
        accepting_orders=True,
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller'''

if old in content:
    content = content.replace(old, new)
    # Add Form and Optional imports
    content = content.replace(
        'from fastapi import APIRouter, Depends, HTTPException',
        'from fastapi import APIRouter, Depends, HTTPException, Form'
    )
    content = content.replace(
        'from typing import List',
        'from typing import List, Optional'
    )
    open(r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\sellers.py', 'w', encoding='utf-8').write(content)
    print("✅ sellers.py updated with /profile endpoint")
else:
    print("❌ Pattern not found")
    print(content[:300])
