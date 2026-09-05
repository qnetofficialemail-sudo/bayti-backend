import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE orders ADD COLUMN confirmed_at TIMESTAMP WITH TIME ZONE"))
        print("Added confirmed_at to orders")
    except Exception as e:
        print(f"orders confirmed_at: {e}")
    try:
        conn.execute(text("ALTER TABLE seller_profiles ADD COLUMN avg_response_minutes FLOAT"))
        print("Added avg_response_minutes to seller_profiles")
    except Exception as e:
        print(f"seller_profiles avg_response_minutes: {e}")
    conn.commit()
print("Migration complete")
