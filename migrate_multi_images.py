import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    for col in ["image_2", "image_3", "image_4", "image_5"]:
        try:
            conn.execute(text(f"ALTER TABLE products ADD COLUMN {col} TEXT"))
            print(f"Done - {col} added")
        except Exception as e:
            print(f"{col}: {e}")
    try:
        conn.execute(text("ALTER TABLE products ADD COLUMN primary_image_index INTEGER DEFAULT 0"))
        print("Done - primary_image_index added")
    except Exception as e:
        print(f"primary_image_index: {e}")
    conn.commit()
print("Migration complete")
