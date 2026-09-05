path = r'C:\Users\Dell\Desktop\homemarketplace\backend\routers\products.py'
content = open(path, encoding='utf-8').read()

old = '''    query = db.query(Product).join(SellerProfile).filter(
        Product.is_available == True,
        SellerProfile.is_approved == True
    )'''

new = '''    from models.user import Category
    # Get active category IDs
    active_cat_ids = [c.id for c in db.query(Category.id).filter(Category.is_active == True).all()]
    query = db.query(Product).join(SellerProfile).filter(
        Product.is_available == True,
        SellerProfile.is_approved == True,
        Product.category_id.in_(active_cat_ids)
    )'''

if old in content:
    content = content.replace(old, new)
    open(path, 'w', encoding='utf-8').write(content)
    print("✅ Category filter fixed using subquery approach")
else:
    print("❌ Pattern not found")
