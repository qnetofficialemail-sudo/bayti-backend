import sys
sys.path.insert(0, '.')
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Add name_ar column to categories if not exists
try:
    db.execute(text("ALTER TABLE categories ADD COLUMN name_ar TEXT"))
    db.commit()
    print("Added name_ar column to categories")
except:
    print("Column already exists")

# Arabic category translations
categories_ar = {
    "Home Cooked Meals": "وجبات منزلية",
    "Desserts & Sweets": "حلويات ومعجنات",
    "Baked Goods": "مخبوزات",
    "Healthy Food": "أكل صحي",
    "Juices & Drinks": "عصائر ومشروبات",
    "Handmade Crafts": "حرف يدوية",
    "Beauty & Skincare": "جمال وعناية",
    "Perfumes & Candles": "عطور وشموع",
}

for name_en, name_ar in categories_ar.items():
    db.execute(
        text("UPDATE categories SET name_ar = :name_ar WHERE name = :name"),
        {"name_ar": name_ar, "name": name_en}
    )
    print(f"✅ {name_en} -> {name_ar}")

db.commit()
db.close()
print("Categories translated!")
