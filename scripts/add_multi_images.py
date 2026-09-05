import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add image_2..5 + primary_image_index to Product model ──
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

old_img = '    image_url = Column(String, nullable=True)'
new_img = '''    image_url = Column(String, nullable=True)       # primary/main image
    image_2 = Column(String, nullable=True)
    image_3 = Column(String, nullable=True)
    image_4 = Column(String, nullable=True)
    image_5 = Column(String, nullable=True)
    primary_image_index = Column(Integer, default=0)  # 0=image_url,1=image_2,...'''

if 'image_2' not in content:
    if old_img in content:
        content = content.replace(old_img, new_img)
        open(model_path, 'w', encoding='utf-8').write(content)
        print("Done - image_2..5 + primary_image_index added to Product model")
    else:
        print("FAIL - could not find image_url in Product model")
else:
    print("Skip - already exists")

# ── 2. Update products router ──
products_path = os.path.join(BACKEND, 'routers', 'products.py')
products = open(products_path, encoding='utf-8').read()

if 'image_2' not in products:
    # Add image_2..5 to create endpoint params
    old_create_img = '    image: Optional[UploadFile] = File(None),\n    time_unit: str = Form("minutes"),'
    new_create_img = '''    image: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    primary_image_index: int = Form(0),
    time_unit: str = Form("minutes"),'''

    # Add upload logic after main image upload
    old_upload = '''        image_url = upload_product_image(file_bytes, filename)
    product = Product('''
    new_upload = '''        image_url = upload_product_image(file_bytes, filename)

    # Upload additional images
    extra_urls = []
    for extra_img in [image_2, image_3, image_4, image_5]:
        if extra_img and extra_img.filename:
            ext2 = extra_img.filename.split(".")[-1]
            fn2 = f"product_{seller.id}_{extra_img.filename.rsplit('.', 1)[0]}_{ext2}"
            fb2 = await extra_img.read()
            extra_urls.append(upload_product_image(fb2, fn2))
        else:
            extra_urls.append(None)

    product = Product('''

    old_product_obj = '        time_unit=time_unit,'
    new_product_obj = '''        time_unit=time_unit,
        image_2=extra_urls[0] if extra_urls else None,
        image_3=extra_urls[1] if len(extra_urls) > 1 else None,
        image_4=extra_urls[2] if len(extra_urls) > 2 else None,
        image_5=extra_urls[3] if len(extra_urls) > 3 else None,
        primary_image_index=primary_image_index,'''

    if old_create_img in products:
        products = products.replace(old_create_img, new_create_img)
        print("Done - image params added to create endpoint")
    else:
        print("FAIL - could not find create image param")

    if old_upload in products:
        products = products.replace(old_upload, new_upload)
        print("Done - extra image upload logic added")
    else:
        print("FAIL - could not find upload block")

    if old_product_obj in products:
        products = products.replace(old_product_obj, new_product_obj)
        print("Done - image fields added to Product object")
    else:
        print("FAIL - could not find product obj time_unit")

    # Add images to product output dict
    old_out = '"time_unit": p.time_unit or "minutes",'
    new_out = '''"time_unit": p.time_unit or "minutes",
            "images": [u for u in [p.image_url, p.image_2, p.image_3, p.image_4, p.image_5] if u],
            "primary_image_index": p.primary_image_index or 0,'''

    if old_out in products:
        products = products.replace(old_out, new_out)
        print("Done - images array added to product output")
    else:
        print("FAIL - could not find time_unit in output")

    open(products_path, 'w', encoding='utf-8').write(products)
else:
    print("Skip - image_2 already in products router")

# ── 3. Add set_primary_image endpoint ──
products = open(products_path, encoding='utf-8').read()
set_primary = '''

@router.patch("/{product_id}/primary-image")
def set_primary_image(
    product_id: int,
    index: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.primary_image_index = index
    db.commit()
    return {"primary_image_index": index}
'''

if 'primary-image' not in products:
    products = products.rstrip() + '\n' + set_primary
    open(products_path, 'w', encoding='utf-8').write(products)
    print("Done - set_primary_image endpoint added")
else:
    print("Skip - set_primary_image already exists")

# ── 4. Add update endpoint support for extra images ──
products = open(products_path, encoding='utf-8').read()
if 'image_2' not in products.split('async def update_product')[1][:500] if 'async def update_product' in products else True:
    # Find update endpoint image handling
    old_update_img = '''    if image:
        ext = image.filename.split(".")[-1]
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)'''
    new_update_img = '''    if image and image.filename:
        ext = image.filename.split(".")[-1]
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)
    for i, extra_img in enumerate([image_2, image_3, image_4, image_5], 2):
        if extra_img and extra_img.filename:
            ext2 = extra_img.filename.split(".")[-1]
            fn2 = f"product_{product.seller_id}_extra{i}_{ext2}"
            fb2 = await extra_img.read()
            url = upload_product_image(fb2, fn2)
            setattr(product, f"image_{i}", url)'''

    if old_update_img in products:
        products = products.replace(old_update_img, new_update_img)
        # Also add image_2..5 params to update endpoint
        old_update_param = '    image: Optional[UploadFile] = File(None),\n    db: Session = Depends(get_db),'
        new_update_param = '''    image: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    primary_image_index: Optional[int] = Form(None),
    db: Session = Depends(get_db),'''
        if old_update_param in products:
            products = products.replace(old_update_param, new_update_param)
            print("Done - update endpoint updated with extra images")
        open(products_path, 'w', encoding='utf-8').write(products)

# ── 5. Create migration ──
migrate = '''import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    for col in ["image_2", "image_3", "image_4", "image_5"]:
        try:
            conn.execute(text(f"ALTER TABLE products ADD COLUMN {col} TEXT"))
            print(f"Done - {col} added")
        except Exception as e:
            print(f"{col}: {e}")
    try:
        conn.execute(text("ALTER TABLE products ADD COLUMN primary_image_index INTEGER DEFAULT 0"))
        print("Done - primary_image_index added")
    except Exception as e:
        print(f"primary_image_index: {e}")
    conn.commit()
print("Migration complete")
'''
open(os.path.join(BACKEND, 'migrate_multi_images.py'), 'w', encoding='utf-8').write(migrate)
print("Done - migrate_multi_images.py created")

print("\nAll backend done!")
