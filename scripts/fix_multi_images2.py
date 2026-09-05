import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# ── 1. Add extra image params after stock_quantity ──
old_param = '    time_unit: str = Form("minutes"),\n    stock_quantity: int = Form(-1),'
new_param = '''    time_unit: str = Form("minutes"),
    stock_quantity: int = Form(-1),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    primary_image_index: int = Form(0),'''

if 'image_2: Optional[UploadFile]' not in content:
    if old_param in content:
        content = content.replace(old_param, new_param)
        print("Done - extra image params added")
    else:
        print("FAIL - stock_quantity param not found")
        idx = content.find('stock_quantity')
        print(repr(content[max(0,idx-100):idx+100]))
else:
    print("Skip - already has image_2 param")

# ── 2. Find actual output dict pattern ──
# Look for what's actually in the output
idx = content.find('"time_unit"')
if idx > 0:
    print("Found time_unit output at:", idx)
    print(repr(content[idx:idx+200]))
else:
    # Check if output uses model directly (response_model=ProductOut)
    print("No time_unit in output dict - likely uses ORM model directly")
    # Add images to the product schema instead
    # Find schemas
    schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
    if os.path.exists(schema_path):
        schemas = open(schema_path, encoding='utf-8').read()
        print("Schema file found, checking ProductOut...")
        idx2 = schemas.find('ProductOut')
        if idx2 > 0:
            print(repr(schemas[idx2:idx2+300]))

open(products_path, 'w', encoding='utf-8').write(content)
print("Saved")
