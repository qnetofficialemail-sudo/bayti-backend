BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
import os

path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(path, encoding='utf-8').read()

# Add OR filter for name_ar and description
old = '    if search:\n        query = query.filter(Product.name.ilike(f"%{search}%"))'
new = '''    if search:
        from sqlalchemy import or_
        query = query.filter(or_(
            Product.name.ilike(f"%{search}%"),
            Product.name_ar.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
            Product.description_ar.ilike(f"%{search}%"),
        ))'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Arabic search fixed!")
else:
    print("❌ Pattern not found")
