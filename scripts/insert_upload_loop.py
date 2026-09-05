import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

old_block = 'image_url = upload_product_image(file_bytes, filename)\n\n    product = Product('
new_block = '''image_url = upload_product_image(file_bytes, filename)

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

    product = Product('''

if 'Upload additional images' not in content:
    if old_block in content:
        content = content.replace(old_block, new_block)
        open(products_path, 'w', encoding='utf-8').write(content)
        print("Done - upload loop inserted")
    else:
        print("FAIL - block not found")
        # Try finding just the transition
        idx = content.find('image_url = upload_product_image(file_bytes, filename)')
        idx2 = content.find('product = Product(', idx)
        print(repr(content[idx:idx2+20]))
else:
    print("Skip - upload loop already exists")
