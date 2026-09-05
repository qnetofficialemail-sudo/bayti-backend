import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'

# ── 1. Add image fields to ProductOut schema ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
content = open(schema_path, encoding='utf-8').read()

old_schema = '''    image_url: Optional[str]
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    is_featured: bool = False
    sold_count: int = 0
    created_at: Optional[datetime] = None'''

new_schema = '''    image_url: Optional[str]
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    image_5: Optional[str] = None
    primary_image_index: int = 0
    time_unit: Optional[str] = "minutes"
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    is_featured: bool = False
    sold_count: int = 0
    created_at: Optional[datetime] = None'''

if 'image_2' not in content:
    if old_schema in content:
        content = content.replace(old_schema, new_schema)
        open(schema_path, 'w', encoding='utf-8').write(content)
        print("Done - image fields added to ProductOut schema")
    else:
        print("FAIL - could not find ProductOut fields")
else:
    print("Skip - already in schema")

# ── 2. Fix the upload loop in products.py ──
# The extra_urls block exists but is misplaced - it's inside the `if image:` block
# Need to verify and fix
products_path = os.path.join(BACKEND, 'routers', 'products.py')
products = open(products_path, encoding='utf-8').read()

# Find and show the area around extra_urls
idx = products.find('extra_urls')
if idx > 0:
    print("\n=== extra_urls context ===")
    print(repr(products[max(0,idx-200):idx+400]))
else:
    print("extra_urls not found in products.py")

    # Add the upload loop - find where image_url upload ends
    old_upload = '        image_url = upload_product_image(file_bytes, filename)\n        image_2=extra_urls[0] if extra_urls else None,'
    new_upload = '''        image_url = upload_product_image(file_bytes, filename)

    # Upload additional images
    extra_urls = []
    for extra_img in [image_2, image_3, image_4, image_5]:
        if extra_img and extra_img.filename:
            ext2 = extra_img.filename.split(".")[-1]
            fn2 = f"product_extra_{extra_img.filename.rsplit('.', 1)[0]}"
            fb2 = await extra_img.read()
            extra_urls.append(upload_product_image(fb2, fn2))
        else:
            extra_urls.append(None)
        image_2=extra_urls[0] if extra_urls else None,'''

    if old_upload in products:
        products = products.replace(old_upload, new_upload)
        open(products_path, 'w', encoding='utf-8').write(products)
        print("Done - upload loop fixed")
    else:
        print("FAIL - upload pattern not found")
        # Show what's around image_2=extra_urls
        idx2 = products.find('image_2=extra_urls')
        if idx2 > 0:
            print(repr(products[max(0,idx2-300):idx2+100]))
