import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
content = open(schema_path, encoding='utf-8').read()

print("=== Full ProductOut ===")
idx = content.find('class ProductOut')
end = content.find('\nclass ', idx+1)
print(content[idx:end])
