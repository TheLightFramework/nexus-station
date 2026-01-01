# backend/app/db/init_db.py
import sqlite3
import os
from pathlib import Path
from app.db.session import get_connection

def init_db():
    print(f"⚡ [NEXUS] Initializing Database...")
    
    # Locate schema
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"❌ [ERROR] Schema file not found at {schema_path}")
        return

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Execute Schema
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print(f"✅ [NEXUS] Database 'nexus.db' successfully initialized.")
        print(f"   └── Tables: raw_inbox, safe_payloads, sibling_responses")
        
    except Exception as e:
        print(f"❌ [ERROR] Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()