import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# ── 1. Add time_unit to Product model ──
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

old_prep = '    preparation_time = Column(Integer, default=60)'
new_prep = '    preparation_time = Column(Integer, default=60)\n    time_unit = Column(String, default="minutes")  # minutes, hours, days'

if 'time_unit' not in content:
    if old_prep in content:
        content = content.replace(old_prep, new_prep)
        open(model_path, 'w', encoding='utf-8').write(content)
        print("Done - time_unit added to Product model")
    else:
        print("FAIL - could not find preparation_time in Product model")
else:
    print("Skip - time_unit already exists")

# ── 2. Add time_unit to products router (create + update) ──
products_path = os.path.join(BACKEND, 'routers', 'products.py')
products = open(products_path, encoding='utf-8').read()

# Add to create endpoint
old_create = '    preparation_time: int = Form(60),'
new_create = '    preparation_time: int = Form(60),\n    time_unit: str = Form("minutes"),'

old_create_obj = '        preparation_time=preparation_time,'
new_create_obj = '        preparation_time=preparation_time,\n        time_unit=time_unit,'

# Add to product output
old_return = '"preparation_time": p.preparation_time,'
new_return = '"preparation_time": p.preparation_time,\n            "time_unit": p.time_unit or "minutes",'

if 'time_unit' not in products:
    products = products.replace(old_create, new_create)
    products = products.replace(old_create_obj, new_create_obj)
    if old_return in products:
        products = products.replace(old_return, new_return)
    open(products_path, 'w', encoding='utf-8').write(products)
    print("Done - time_unit added to products router")
else:
    print("Skip - time_unit already in products router")

# ── 3. Make schedule optional in sellers router ──
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
sellers = open(sellers_path, encoding='utf-8').read()

# Find is_seller_open and make it return open if no schedule set
old_schedule = 'def is_seller_open(seller) -> dict:'
if old_schedule in sellers:
    idx = sellers.find(old_schedule)
    # Find the function body
    func_end = sellers.find('\ndef ', idx + 1)
    func_body = sellers[idx:func_end]
    
    # Add early return if no schedule configured
    old_func_start = 'def is_seller_open(seller) -> dict:\n'
    new_func_start = '''def is_seller_open(seller) -> dict:
    # If seller has no schedule configured, always open
    if not seller.available_days and not seller.available_from:
        return {"is_open": True, "message": ""}
'''
    if 'If seller has no schedule' not in sellers:
        sellers = sellers.replace(old_func_start, new_func_start, 1)
        open(sellers_path, 'w', encoding='utf-8').write(sellers)
        print("Done - schedule made optional in sellers router")
    else:
        print("Skip - schedule already optional")
else:
    print("FAIL - is_seller_open not found in sellers.py")

# ── 4. Create Railway migration ──
migrate = '''import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE products ADD COLUMN time_unit VARCHAR DEFAULT 'minutes'"))
        print("Done - time_unit added to products")
    except Exception as e:
        print(f"time_unit: {e}")
    conn.commit()
print("Migration complete")
'''
open(os.path.join(BACKEND, 'migrate_time_unit.py'), 'w', encoding='utf-8').write(migrate)
print("Done - migrate_time_unit.py created")

# ── 5. Update AddProduct.tsx - add time_unit selector ──
add_path = os.path.join(FRONTEND, 'src', 'pages', 'AddProduct.tsx')
add = open(add_path, encoding='utf-8').read()

old_proc_state = 'processing_days: "3"'
new_proc_state = 'processing_days: "3", time_unit: "days"'

old_proc_field = '''          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{isArabic ? "أيام التجهيز" : "Processing days"}</label>
            <input type="number" value={form.processing_days} onChange={e => setForm(f => ({ ...f, processing_days: e.target.value }))} min="1" max="30"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-orange-300" />
          </div>'''

new_proc_field = '''          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{isArabic ? "وقت التجهيز" : "Processing time"}</label>
            <div className="flex gap-2">
              <input type="number" value={form.processing_days} onChange={e => setForm(f => ({ ...f, processing_days: e.target.value }))} min="1" max="999"
                className="flex-1 border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-orange-300" />
              <select value={form.time_unit} onChange={e => setForm(f => ({ ...f, time_unit: e.target.value }))}
                className="border border-gray-200 rounded-xl px-3 py-3 focus:outline-none focus:ring-2 focus:ring-orange-300 bg-white text-sm">
                <option value="minutes">{isArabic ? "دقيقة" : "mins"}</option>
                <option value="hours">{isArabic ? "ساعة" : "hrs"}</option>
                <option value="days">{isArabic ? "يوم" : "days"}</option>
              </select>
            </div>
          </div>'''

old_submit_prep = 'data.append("preparation_time", form.processing_days);'
new_submit_prep = 'data.append("preparation_time", form.processing_days);\n      data.append("time_unit", form.time_unit);'

if 'time_unit' not in add:
    add = add.replace(old_proc_state, new_proc_state)
    if old_proc_field in add:
        add = add.replace(old_proc_field, new_proc_field)
        print("Done - time_unit selector added to AddProduct")
    else:
        print("FAIL - could not find processing days field in AddProduct")
    add = add.replace(old_submit_prep, new_submit_prep)
    open(add_path, 'w', encoding='utf-8').write(add)
else:
    print("Skip - time_unit already in AddProduct")

# ── 6. Update ProductDetail.tsx - show time_unit correctly ──
detail_path = os.path.join(FRONTEND, 'src', 'pages', 'ProductDetail.tsx')
detail = open(detail_path, encoding='utf-8').read()

# Find preparation_time display and make it unit-aware
old_prep_display = 'product.preparation_time}'
if old_prep_display in detail and 'time_unit' not in detail:
    # Replace all occurrences of preparation_time display
    detail = detail.replace(
        '{product.preparation_time}',
        '{product.preparation_time} {product.time_unit === "days" ? (isArabic ? "يوم" : "days") : product.time_unit === "hours" ? (isArabic ? "ساعة" : "hrs") : (isArabic ? "د" : "min")}'
    )
    open(detail_path, 'w', encoding='utf-8').write(detail)
    print("Done - time_unit display added to ProductDetail")
else:
    print("Skip - time_unit already in ProductDetail or prep_time not found")

print("\nAll done!")
