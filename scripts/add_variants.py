import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'

# ── 1. Add ProductVariant model ──
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

variant_model = '''

class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)        # e.g. "Size", "Color", "Scent"
    name_ar = Column(String, nullable=True)      # Arabic name
    options = Column(Text, nullable=False)       # JSON: [{"label":"S","price_adj":0},{"label":"M","price_adj":5}]
    is_required = Column(Boolean, default=True)
    product = relationship("Product", back_populates="variants")
'''

if 'ProductVariant' not in content:
    # Add relationship to Product first
    old_product_rel = '    order_items = relationship("OrderItem", back_populates="product")'
    new_product_rel = '    order_items = relationship("OrderItem", back_populates="product")\n    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")'
    content = content.replace(old_product_rel, new_product_rel)
    content = content.rstrip() + '\n' + variant_model
    open(model_path, 'w', encoding='utf-8').write(content)
    print("Done - ProductVariant model added")
else:
    print("Skip - ProductVariant already exists")

# ── 2. Add variant field to OrderItem ──
content = open(model_path, encoding='utf-8').read()
old_orderitem = '''class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)'''

new_orderitem = '''class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    selected_variants = Column(Text, nullable=True)  # JSON: {"Size":"M","Color":"Black"}'''

if 'selected_variants' not in content:
    if old_orderitem in content:
        content = content.replace(old_orderitem, new_orderitem)
        open(model_path, 'w', encoding='utf-8').write(content)
        print("Done - selected_variants added to OrderItem")
    else:
        print("FAIL - could not find OrderItem class")
else:
    print("Skip - selected_variants already exists")

# ── 3. Add variant endpoints to products router ──
products_path = os.path.join(BACKEND, 'routers', 'products.py')
products = open(products_path, encoding='utf-8').read()

variant_endpoints = '''

# ── Product Variants ──
@router.get("/{product_id}/variants")
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    from models.user import ProductVariant
    variants = db.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()
    return [{"id": v.id, "name": v.name, "name_ar": v.name_ar, "options": v.options, "is_required": v.is_required} for v in variants]


@router.post("/{product_id}/variants")
def add_product_variant(
    product_id: int,
    name: str = Form(...),
    name_ar: str = Form(""),
    options: str = Form(...),  # JSON string
    is_required: bool = Form(True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    from models.user import ProductVariant
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller or product.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    variant = ProductVariant(
        product_id=product_id,
        name=name,
        name_ar=name_ar,
        options=options,
        is_required=is_required,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return {"id": variant.id, "name": variant.name, "options": variant.options}


@router.delete("/{product_id}/variants/{variant_id}")
def delete_product_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    from models.user import ProductVariant
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    db.delete(variant)
    db.commit()
    return {"message": "Variant deleted"}
'''

if 'product_variants' not in products:
    # Check imports
    if 'get_current_seller' not in products:
        products = products.replace(
            'from core.auth import get_current_user',
            'from core.auth import get_current_user, get_current_seller'
        )
    if 'SellerProfile' not in products:
        products = products.replace(
            'from models.user import',
            'from models.user import SellerProfile,'
        )
    products = products.rstrip() + '\n' + variant_endpoints
    open(products_path, 'w', encoding='utf-8').write(products)
    print("Done - variant endpoints added to products.py")
else:
    print("Skip - variants already in products.py")

# ── 4. Add main.py import for ProductVariant ──
main_path = os.path.join(BACKEND, 'main.py')
main = open(main_path, encoding='utf-8').read()
if 'ProductVariant' not in main:
    main = main.replace(
        'from models.user import User, SellerProfile, Category, Product, Order, OrderItem, SellerApplication',
        'from models.user import User, SellerProfile, Category, Product, Order, OrderItem, SellerApplication, ProductVariant'
    )
    open(main_path, 'w', encoding='utf-8').write(main)
    print("Done - ProductVariant added to main.py imports")
else:
    print("Skip - ProductVariant already in main.py")

# ── 5. Create Railway migration script ──
migrate = '''import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_variants (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                name_ar VARCHAR,
                options TEXT NOT NULL,
                is_required BOOLEAN DEFAULT TRUE
            )
        """))
        print("Done - product_variants table created")
    except Exception as e:
        print(f"product_variants: {e}")
    try:
        conn.execute(text("ALTER TABLE order_items ADD COLUMN selected_variants TEXT"))
        print("Done - selected_variants added to order_items")
    except Exception as e:
        print(f"selected_variants: {e}")
    conn.commit()
print("Migration complete")
'''
open(os.path.join(BACKEND, 'migrate_variants.py'), 'w', encoding='utf-8').write(migrate)
print("Done - migrate_variants.py created")
