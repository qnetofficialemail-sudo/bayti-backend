import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Fix ProductOut schema ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()

old_out = '''class ProductOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str]
    description_ar: Optional[str] = None
    price: float
    image_url: Optional[str]
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    is_featured: bool = False
    sold_count: int = 0
    created_at: Optional[datetime] = None
    category: Optional[CategoryOut]
    seller: Optional[SellerProfileOut] = None
    class Config:
        from_attributes = True'''

new_out = '''class ProductOut(BaseModel):
    id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str]
    description_ar: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    image_2: Optional[str] = None
    image_3: Optional[str] = None
    image_4: Optional[str] = None
    image_5: Optional[str] = None
    primary_image_index: int = 0
    time_unit: Optional[str] = "minutes"
    is_available: bool
    preparation_time: int
    stock_quantity: int = -1
    track_stock: int = 0
    is_featured: bool = False
    sold_count: int = 0
    created_at: Optional[datetime] = None
    category: Optional[CategoryOut]
    seller: Optional[SellerProfileOut] = None
    class Config:
        from_attributes = True'''

if 'image_2' not in schema:
    if old_out in schema:
        schema = schema.replace(old_out, new_out)
        open(schema_path, 'w', encoding='utf-8').write(schema)
        print("Done - ProductOut schema updated with image fields")
    else:
        print("FAIL - ProductOut not found")
        idx = schema.find('class ProductOut')
        print(repr(schema[idx:idx+200]))
else:
    print("Skip - image_2 already in schema")

# ── 2. Find correct product edit button in SellerDashboard ──
dashboard_path = os.path.join(FRONTEND, 'src', 'pages', 'SellerDashboard.tsx')
dashboard = open(dashboard_path, encoding='utf-8').read()

# Find product edit link pattern
idx = dashboard.find('/edit`}')
if idx < 0:
    idx = dashboard.find("products/${")
print("\n=== Product edit area ===")
if idx > 0:
    print(repr(dashboard[max(0,idx-300):idx+200]))
else:
    # Find where products are listed
    idx2 = dashboard.find('p.name')
    print(repr(dashboard[max(0,idx2-100):idx2+400]))
