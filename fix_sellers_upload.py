import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
content = open(sellers_path, encoding='utf-8').read()

old = '''    if min_order_amount is not None: seller.min_order_amount = min_order_amount
    db.commit()
    db.refresh(seller)
    return seller
@router.patch("/schedule"'''

new = '''    if min_order_amount is not None: seller.min_order_amount = min_order_amount
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

if 'upload_seller_logo' not in content:
    if old in content:
        content = content.replace(old, new)
        open(sellers_path, 'w', encoding='utf-8').write(content)
        print("Done - image upload logic added")
    else:
        print("FAIL - pattern not found")
        idx = content.find('min_order_amount is not None')
        print(repr(content[idx:idx+200]))
else:
    print("Skip - already there")
