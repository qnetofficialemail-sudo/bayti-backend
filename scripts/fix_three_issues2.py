import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Fix ProductOut schema - add missing fields ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()

# Find ProductOut class and show it
idx = schema.find('class ProductOut')
end = schema.find('\nclass ', idx+1)
product_out = schema[idx:end]
print("=== ProductOut ===")
print(product_out[:600])

# Add primary_image_index and time_unit after image_2 block
old_schema = '    image_2: Optional[str] = None\n    image_3: Optional[str] = None\n    image_4: Optional[str] = None\n    image_5: Optional[str] = None'
new_schema = '    image_2: Optional[str] = None\n    image_3: Optional[str] = None\n    image_4: Optional[str] = None\n    image_5: Optional[str] = None\n    primary_image_index: int = 0\n    time_unit: Optional[str] = "minutes"'

if 'primary_image_index' not in schema:
    if old_schema in schema:
        schema = schema.replace(old_schema, new_schema)
        open(schema_path, 'w', encoding='utf-8').write(schema)
        print("Done - primary_image_index and time_unit added to ProductOut")
    else:
        print("FAIL - image_2 block not found in schema")
        # Try adding after image_url
        old2 = '    image_url: Optional[str] = None\n'
        if old2 in schema:
            new2 = '    image_url: Optional[str] = None\n    image_2: Optional[str] = None\n    image_3: Optional[str] = None\n    image_4: Optional[str] = None\n    image_5: Optional[str] = None\n    primary_image_index: int = 0\n    time_unit: Optional[str] = "minutes"\n'
            schema = schema.replace(old2, new2)
            open(schema_path, 'w', encoding='utf-8').write(schema)
            print("Done - all image fields added to ProductOut (fallback)")
else:
    print("Skip - primary_image_index already in schema")

# ── 2. Fix SellerDashboard - find correct edit button pattern ──
dashboard_path = os.path.join(FRONTEND, 'src', 'pages', 'SellerDashboard.tsx')
dashboard = open(dashboard_path, encoding='utf-8').read()

# Find navigate to edit
idx2 = dashboard.find('/seller/products/')
if idx2 > 0:
    print("\n=== SellerDashboard edit area ===")
    print(repr(dashboard[max(0,idx2-200):idx2+200]))

# ── 3. Fix EditProduct - add existing images display ──
edit_path = os.path.join(FRONTEND, 'src', 'pages', 'EditProduct.tsx')
edit = open(edit_path, encoding='utf-8').read()

# The label is "Photo" not "Current Image"
old_photo = '          <label className="block text-sm font-medium text-gray-700 mb-2">{isArabic ? "\u0627\u0644\u0635\u0648\u0631\u0629" : "Photo"}</label>'
new_photo = '''          <label className="block text-sm font-medium text-gray-700 mb-2">{isArabic ? "\u0627\u0644\u0635\u0648\u0631" : "Photos"}</label>
          {/* Show existing images */}
          <div className="flex gap-2 flex-wrap mb-2">
            {[currentImage].filter(Boolean).map((img: string, i: number) => (
              <div key={i} className="relative">
                <img src={img.startsWith("http") ? img : `https://web-production-63685.up.railway.app${img}`}
                  alt="Current" className="w-16 h-16 object-cover rounded-xl border border-orange-300" />
                <span className="absolute bottom-0 left-0 right-0 text-center text-xs bg-orange-500 text-white rounded-b-xl py-0.5">Main</span>
              </div>
            ))}
          </div>'''

if 'existing images' not in edit:
    if old_photo in edit:
        edit = edit.replace(old_photo, new_photo)
        open(edit_path, 'w', encoding='utf-8').write(edit)
        print("Done - existing image shown in EditProduct")
    else:
        print("FAIL - Photo label not found in EditProduct")
        idx3 = edit.find('"Photo"')
        if idx3 > 0:
            print(repr(edit[max(0,idx3-200):idx3+100]))
else:
    print("Skip - already updated EditProduct")
