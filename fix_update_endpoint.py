import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# Add missing params to update endpoint
old_params = '''    preparation_time: Optional[int] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    track_stock: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):'''

new_params = '''    preparation_time: Optional[int] = Form(None),
    time_unit: Optional[str] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    track_stock: Optional[bool] = Form(None),
    primary_image_index: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):'''

# Add save logic after the existing image upload block
old_save = '''    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)
    db.commit()'''

new_save = '''    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)
    if time_unit is not None: product.time_unit = time_unit
    if primary_image_index is not None: product.primary_image_index = primary_image_index
    for i, extra_img in enumerate([image_2, image_3, image_4, image_5], 2):
        if extra_img and extra_img.filename:
            ext2 = extra_img.filename.split(".")[-1]
            fn2 = f"product_extra_{product.id}_{i}_{ext2}"
            fb2 = await extra_img.read()
            setattr(product, f"image_{i}", upload_product_image(fb2, fn2))
    db.commit()'''

if 'time_unit: Optional[str] = Form(None)' not in content:
    if old_params in content:
        content = content.replace(old_params, new_params)
        print("Done - update endpoint params added")
    else:
        print("FAIL - update params pattern not found")

if 'time_unit is not None' not in content:
    if old_save in content:
        content = content.replace(old_save, new_save)
        print("Done - update endpoint save logic added")
    else:
        print("FAIL - update save pattern not found")
        idx = content.find('product.image_url = upload_product_image')
        print(repr(content[max(0,idx-50):idx+200]))

open(products_path, 'w', encoding='utf-8').write(content)
print("Saved products.py")
