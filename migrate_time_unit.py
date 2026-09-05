import sys
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
