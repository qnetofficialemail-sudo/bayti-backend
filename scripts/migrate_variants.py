import sys
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
