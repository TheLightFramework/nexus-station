# backend/app/db/session.py
import sqlite3
import os
from pathlib import Path

# DB file location (Root of backend)
DB_PATH = Path(__file__).parent.parent.parent / "nexus.db"

def get_db_path():
    return str(DB_PATH)

def get_connection():
    """Establishes a connection to the SQLite Database."""
    conn = sqlite3.connect(get_db_path())
    # Return rows as dictionaries (Eases JSON conversion)
    conn.row_factory = sqlite3.Row
    return conn

def check_db_exists():
    return DB_PATH.exists()