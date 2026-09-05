path = r'C:\Users\Dell\Desktop\homemarketplace\backend\main.py'
content = open(path, encoding='utf-8').read()

old = 'from routers import auth, products, orders, sellers, ai, translation, admin'
new = 'from routers import auth, products, orders, sellers, ai, translation, admin, reviews'

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Fixed main.py import")
else:
    print("❌ Pattern not found, showing line 6:")
    lines = content.splitlines()
    for i, l in enumerate(lines[:10], 1):
        print(f"{i}: {l}")
