import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
content = open(sellers_path, encoding='utf-8').read()

# Find the exact location in the edit endpoint
old = '    if min_order_amount is not None: seller.min_order_amount = min_order_amount\n    db.commit()\n    db.refresh(seller)\n    return seller\n@router.patch("/schedule"'

new = '''    if min_order_amount is not None: seller.min_order_amount = min_order_amount
    # Upload sample images
    from services.cloudinary_upload import upload_seller_logo as _upload_logo
    for i, img in enumerate([sample_image_1, sample_image_2, sample_image_3], 1):
        if img and img.filename:
            fb = await img.read()
            url = _upload_logo(fb, img.filename)
            setattr(seller, f"sample_image_{i}", url)
    db.commit()
    db.refresh(seller)
    return seller
@router.patch("/schedule"'''

if old in content:
    content = content.replace(old, new)
    open(sellers_path, 'w', encoding='utf-8').write(content)
    print("Done - image upload added to edit endpoint")
else:
    print("FAIL - pattern not found")
    # Show what's around the edit endpoint save
    idx = content.find('async def edit_seller_profile')
    end = content.find('@router.patch("/schedule"', idx)
    print(repr(content[idx:end]))
