import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# Find the exact create endpoint image param line
# From inspection: time_unit comes BEFORE image in the params
old_param = '    time_unit: str = Form("minutes"),\n    image: Optional[UploadFile] = File(None),'
new_param = '''    time_unit: str = Form("minutes"),
    image: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    primary_image_index: int = Form(0),'''

if 'image_2: Optional[UploadFile]' not in content:
    if old_param in content:
        content = content.replace(old_param, new_param)
        print("Done - extra image params added to create endpoint")
    else:
        print("FAIL - param pattern not found, trying alternate...")
        # Try with different spacing
        idx = content.find('time_unit: str = Form("minutes")')
        if idx > 0:
            eol = content.find('\n', idx)
            next_line_end = content.find('\n', eol + 1)
            print(repr(content[idx:next_line_end+1]))
        else:
            print("FAIL - time_unit not found at all")
else:
    print("Skip - extra image params already exist")

# Find the upload block and add extra image uploads after it
old_upload = '''    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        file_bytes = await image.read()
        image_url = upload_product_image(file_bytes, filename)
        image_2=extra_urls[0] if extra_urls else None,'''

# Actually the issue is the extra_urls block is missing - image_2 fields exist but
# the upload loop that creates extra_urls doesn't exist
# Find where image_url upload ends and Product( begins

old_upload2 = '''        image_url = upload_product_image(file_bytes, filename)
        image_2=extra_urls[0] if extra_urls else None,'''

new_upload2 = '''        image_url = upload_product_image(file_bytes, filename)

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
        image_2=extra_urls[0] if extra_urls else None,'''

if 'extra_urls' not in content:
    if old_upload2 in content:
        content = content.replace(old_upload2, new_upload2)
        print("Done - extra image upload loop added")
    else:
        # Find the exact pattern
        idx2 = content.find('image_url = upload_product_image(file_bytes, filename)')
        if idx2 > 0:
            # Find what comes after
            after = content[idx2:idx2+300]
            print("Found after upload_product_image:")
            print(repr(after))
        else:
            print("FAIL - upload_product_image not found")
else:
    print("Skip - extra_urls already exists")

# Add images array to product output
old_out = '"primary_image_index": p.primary_image_index or 0,'
if old_out not in content:
    # Find where product output dict is built
    old_out2 = '"time_unit": p.time_unit or "minutes",'
    new_out2 = '''"time_unit": p.time_unit or "minutes",
            "images": [u for u in [p.image_url, p.image_2, p.image_3, p.image_4, p.image_5] if u],
            "primary_image_index": p.primary_image_index or 0,'''
    if old_out2 in content:
        content = content.replace(old_out2, new_out2)
        print("Done - images array added to product output")
    else:
        print("FAIL - time_unit output not found")
else:
    print("Skip - images array already in output")

open(products_path, 'w', encoding='utf-8').write(content)
print("\nSaved products.py")
