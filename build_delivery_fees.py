import sys, os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

EMIRATES = ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]

# ── 1. Add delivery fee columns to SellerProfile model ──
model_path = os.path.join(BACKEND, 'models', 'user.py')
content = open(model_path, encoding='utf-8').read()

# Add delivery_fees JSON column after delivery_type
old_delivery = '    delivery_type = Column(String, nullable=True)     # "self" or "bayti"'
new_delivery = '''    delivery_type = Column(String, nullable=True)     # "self" or "bayti"
    delivery_fees = Column(Text, nullable=True)       # JSON: {"Dubai":15,"Sharjah":20,...} null=not available'''

if 'delivery_fees' not in content:
    if old_delivery in content:
        content = content.replace(old_delivery, new_delivery)
        open(model_path, 'w', encoding='utf-8').write(content)
        print("Done - delivery_fees column added to SellerProfile")
    else:
        print("FAIL - delivery_type line not found in model")
else:
    print("Skip - delivery_fees already in model")

# ── 2. Add delivery_fees to sellers public endpoint ──
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
sellers = open(sellers_path, encoding='utf-8').read()

old_rating = '"rating": seller.rating,'
new_rating = '"rating": seller.rating,\n        "delivery_fees": seller.delivery_fees,'

if '"delivery_fees"' not in sellers:
    if old_rating in sellers:
        sellers = sellers.replace(old_rating, new_rating)
        open(sellers_path, 'w', encoding='utf-8').write(sellers)
        print("Done - delivery_fees added to seller public endpoint")
    else:
        print("FAIL - rating line not found in sellers.py")
else:
    print("Skip - delivery_fees already in sellers.py")

# ── 3. Add delivery_fees to edit endpoint ──
sellers = open(sellers_path, encoding='utf-8').read()
old_min = '    min_order_amount: Optional[float] = Form(None),'
new_min = '    min_order_amount: Optional[float] = Form(None),\n    delivery_fees: Optional[str] = Form(None),  # JSON string'

old_save_min = '    if min_order_amount is not None: seller.min_order_amount = min_order_amount\n    # Upload sample images'
new_save_min = '    if min_order_amount is not None: seller.min_order_amount = min_order_amount\n    if delivery_fees is not None: seller.delivery_fees = delivery_fees\n    # Upload sample images'

if 'delivery_fees: Optional[str] = Form' not in sellers:
    sellers = sellers.replace(old_min, new_min)
    sellers = sellers.replace(old_save_min, new_save_min)
    open(sellers_path, 'w', encoding='utf-8').write(sellers)
    print("Done - delivery_fees added to edit endpoint")
else:
    print("Skip - already in edit endpoint")

# ── 4. Add delivery_fees to SellerProfileOut schema ──
schema_path = os.path.join(BACKEND, 'schemas', 'schemas.py')
schema = open(schema_path, encoding='utf-8').read()

old_schema_rating = '    rating: float = 0.0'
new_schema_rating = '    rating: float = 0.0\n    delivery_fees: Optional[str] = None'

if 'delivery_fees' not in schema:
    if old_schema_rating in schema:
        schema = schema.replace(old_schema_rating, new_schema_rating)
        open(schema_path, 'w', encoding='utf-8').write(schema)
        print("Done - delivery_fees added to SellerProfileOut schema")
    else:
        print("FAIL - rating not found in schema")
        idx = schema.find('class SellerProfileOut')
        print(repr(schema[idx:idx+300]))
else:
    print("Skip - delivery_fees already in schema")

# ── 5. Create DB migration ──
migrate = '''import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE seller_profiles ADD COLUMN delivery_fees TEXT"))
        print("Done - delivery_fees column added")
    except Exception as e:
        print(f"delivery_fees: {e}")
    conn.commit()
print("Migration complete")
'''
open(os.path.join(BACKEND, 'scripts', 'migrate_delivery_fees.py'), 'w', encoding='utf-8').write(migrate)
print("Done - migration script created")

print("\nBackend done! Now building frontend...")

# ── 6. Add delivery fees section to EditShop.tsx ──
edit_shop_path = os.path.join(FRONTEND, 'src', 'pages', 'EditShop.tsx')
edit_shop = open(edit_shop_path, encoding='utf-8').read()

# Add EMIRATES constant and delivery fees state
old_areas = 'const UAE_AREAS = '
new_content_before = '''const EMIRATES = ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"];

const UAE_AREAS = '''

if 'const EMIRATES' not in edit_shop:
    edit_shop = edit_shop.replace(old_areas, new_content_before)
    print("Done - EMIRATES added to EditShop")

# Add deliveryFees state
old_state = '  const [existingImages, setExistingImages]'
new_state = '  const [deliveryFees, setDeliveryFees] = useState<Record<string, string>>({});\n  const [existingImages, setExistingImages]'

if 'deliveryFees' not in edit_shop:
    edit_shop = edit_shop.replace(old_state, new_state)
    print("Done - deliveryFees state added")

# Load delivery fees from API
old_load = '        setExistingImages([myShop.sample_image_1 || null'
new_load = '        if (myShop.delivery_fees) {\n          try { setDeliveryFees(JSON.parse(myShop.delivery_fees)); } catch {}\n        }\n        setExistingImages([myShop.sample_image_1 || null'

if 'delivery_fees' not in edit_shop:
    edit_shop = edit_shop.replace(old_load, new_load)
    print("Done - delivery fees loading added")

# Add delivery_fees to form submission
old_submit_entries = '      Object.entries(form).forEach(([k, v]) => { if (v !== "") data.append(k, v); });'
new_submit_entries = '      Object.entries(form).forEach(([k, v]) => { if (v !== "") data.append(k, v); });\n      data.append("delivery_fees", JSON.stringify(deliveryFees));'

if 'delivery_fees' not in edit_shop or 'JSON.stringify(deliveryFees)' not in edit_shop:
    edit_shop = edit_shop.replace(old_submit_entries, new_submit_entries)
    print("Done - delivery fees added to form submission")

# Add delivery fees UI before the buttons
old_buttons = '        <div className="flex gap-3">'
new_delivery_ui = '''        {/* Delivery Fees */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            {isArabic ? "\u0631\u0633\u0648\u0645 \u0627\u0644\u062a\u0648\u0635\u064a\u0644" : "Delivery Fees"}
          </label>
          <p className="text-xs text-gray-400 mb-3">
            {isArabic ? "\u062d\u062f\u062f \u0633\u0639\u0631 \u0627\u0644\u062a\u0648\u0635\u064a\u0644 \u0644\u0643\u0644 \u0625\u0645\u0627\u0631\u0629 \u0623\u0648 \u0627\u062a\u0631\u0643\u0647\u0627 \u0641\u0627\u0631\u063a\u064b\u0627 \u0625\u0630\u0627 \u0644\u0627 \u062a\u0648\u0635\u0644 \u0625\u0644\u064a\u0647\u0627" : "Set delivery fee per emirate, or leave empty if you don\\'t deliver there"}
          </p>
          <div className="space-y-2">
            {EMIRATES.map(emirate => (
              <div key={emirate} className="flex items-center gap-3">
                <span className="text-sm text-gray-700 w-36 flex-shrink-0">{emirate}</span>
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs text-gray-400">AED</span>
                  <input
                    type="number"
                    min="0"
                    step="5"
                    value={deliveryFees[emirate] || ""}
                    onChange={e => {
                      const val = e.target.value;
                      setDeliveryFees(prev => {
                        const updated = { ...prev };
                        if (val === "") delete updated[emirate];
                        else updated[emirate] = val;
                        return updated;
                      });
                    }}
                    placeholder={isArabic ? "\u0644\u0627 \u064a\u062a\u0648\u0641\u0631" : "Not available"}
                    className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300"
                  />
                </div>
                {deliveryFees[emirate] && (
                  <span className="text-xs text-green-600 font-medium w-16">AED {deliveryFees[emirate]}</span>
                )}
                {!deliveryFees[emirate] && (
                  <span className="text-xs text-gray-300 w-16">{isArabic ? "\u063a\u064a\u0631 \u0645\u062a\u0627\u062d" : "N/A"}</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3">'''

if 'EMIRATES.map(emirate' not in edit_shop:
    if old_buttons in edit_shop:
        edit_shop = edit_shop.replace(old_buttons, new_delivery_ui, 1)
        print("Done - delivery fees UI added to EditShop")
    else:
        print("FAIL - buttons div not found in EditShop")

open(edit_shop_path, 'w', encoding='utf-8').write(edit_shop)
print("Done - EditShop.tsx saved")

print("\nAll done! Now update ProductDetail.tsx separately.")
