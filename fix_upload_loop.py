import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# Find image_url = upload_product_image and show what comes after
idx = content.find('image_url = upload_product_image(file_bytes, filename)')
print("=== After main image upload ===")
print(repr(content[idx:idx+300]))
