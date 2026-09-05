import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
content = open(sellers_path, encoding='utf-8').read()

# Check current state
idx = content.find('async def edit_seller_profile')
print("Current endpoint:")
print(repr(content[idx:idx+400]))

old = '''async def edit_seller_profile(
    shop_name: Optional[str] = None,
    description: Optional[str] = None,
    area: Optional[str] = None,
    city: Optional[str] = None,
    whatsapp_number: Optional[str] = None,
    instagram_handle: Optional[str] = None,
    min_order_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):'''

new = '''async def edit_seller_profile(
    shop_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    whatsapp_number: Optional[str] = Form(None),
    instagram_handle: Optional[str] = Form(None),
    min_order_amount: Optional[float] = Form(None),
    sample_image_1: Optional[UploadFile] = File(None),
    sample_image_2: Optional[UploadFile] = File(None),
    sample_image_3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):'''

old_save = '''    if min_order_amount is not None: seller.min_order_amount = min_order_amount
    db.commit()
    db.refresh(seller)
    return seller
@router.patch("/schedule"'''

new_save = '''    if min_order_amount is not None: seller.min_order_amount = min_order_amount
    from services.cloudinary_upload import upload_seller_logo
    for i, img in enumerate([sample_image_1, sample_image_2, sample_image_3], 1):
        if img and img.filename:
            fb = await img.read()
            url = upload_seller_logo(fb, img.filename)
            setattr(seller, f"sample_image_{i}", url)
    db.commit()
    db.refresh(seller)
    return seller
@router.patch("/schedule"'''

# Add Form/File/UploadFile imports if missing
if 'Form' not in content:
    content = content.replace(
        'from fastapi import APIRouter, Depends, HTTPException',
        'from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile'
    )
    print("Added Form imports")

if old in content:
    content = content.replace(old, new)
    print("Done - endpoint params updated to Form()")
else:
    print("FAIL - endpoint pattern not found")

if 'upload_seller_logo' not in content:
    if old_save in content:
        content = content.replace(old_save, new_save)
        print("Done - image upload logic added")
    else:
        print("FAIL - save pattern not found")
        idx2 = content.find('min_order_amount is not None')
        print(repr(content[idx2:idx2+200]))
else:
    print("Skip - upload logic already there")

open(sellers_path, 'w', encoding='utf-8').write(content)
print("Saved")
