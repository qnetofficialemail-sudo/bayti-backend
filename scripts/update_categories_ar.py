"""
Run this on Railway console to update category Arabic names directly in the DB.
Copy-paste into Railway Console for the web service.
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./homemarketplace.db")
engine = create_engine(DATABASE_URL)

updates = [
    ("Home Cooked Meals", "وجبات منزلية"),
    ("Desserts & Sweets", "حلويات وسكريات"),
    ("Baked Goods", "مخبوزات"),
    ("Healthy Food", "طعام صحي"),
    ("Juices & Drinks", "عصائر ومشروبات"),
    ("Handmade Crafts", "مشغولات يدوية"),
    ("Beauty & Skincare", "جمال وعناية بالبشرة"),
    ("Perfumes & Candles", "عطور وشموع"),
]

with engine.connect() as conn:
    for name, name_ar in updates:
        result = conn.execute(
            text("UPDATE categories SET name_ar = :name_ar WHERE name = :name"),
            {"name_ar": name_ar, "name": name}
        )
        print(f"{'✅' if result.rowcount > 0 else '⚠️ '} {name} → {name_ar} ({result.rowcount} rows)")
    conn.commit()

print("\n🎉 Categories updated!")
