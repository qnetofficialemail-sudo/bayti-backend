import sys
sys.path.insert(0, ".")
from core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS seller_applications (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                phone VARCHAR,
                area VARCHAR NOT NULL,
                city VARCHAR DEFAULT 'Dubai',
                what_they_sell TEXT NOT NULL,
                doc_1_url TEXT,
                doc_2_url TEXT,
                doc_3_url TEXT,
                status VARCHAR DEFAULT 'pending',
                invite_token VARCHAR UNIQUE,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        print("Done - seller_applications table created")
    except Exception as e:
        print(f"Table: {e}")
    conn.commit()
print("Migration complete")
