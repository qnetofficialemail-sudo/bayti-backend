import os
BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# Find create endpoint
idx = content.find('@router.post("/")')
if idx < 0:
    idx = content.find("@router.post('/')")
print("=== CREATE ENDPOINT (first 80 lines) ===")
section = content[idx:idx+3000]
lines = section.split('\n')
for i, line in enumerate(lines[:80]):
    print(f"{i}: {repr(line)}")
