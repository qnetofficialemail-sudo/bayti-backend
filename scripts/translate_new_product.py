import sys
sys.path.insert(0, '.')
from core.database import SessionLocal
from sqlalchemy import text
from services.translation import translate_product_to_arabic

db = SessionLocal()
rows = db.execute(text("SELECT id, name, description FROM products WHERE name_ar IS NULL OR name_ar = ''")).fetchall()
print(f"Found {len(rows)} untranslated products")
for row in rows:
    product_id, name, description = row[0], row[1], row[2]
    print(f"Translating: {name}")
    result = translate_product_to_arabic(name, description or name)
    if result["success"]:
        db.execute(
            text("UPDATE products SET name_ar = :name_ar, description_ar = :desc_ar WHERE id = :id"),
            {"name_ar": result["name_ar"], "desc_ar": result["description_ar"], "id": product_id}
        )
        print(f"  -> {result['name_ar']}")
db.commit()
db.close()
print("Done!")
