from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import time
from pathlib import Path
from datetime import datetime
import sqlite3
from app.db.session import get_connection

router = APIRouter()

# STORAGE: Simple JSON Line persistence for the Hackathon
LOG_FILE = Path("safety_log.jsonl")

class SafetyEvent(BaseModel):
    timestamp: float
    readable_time: str
    event_type: str  # "PHYSICS_SHIELD" | "IRON_CURTAIN"
    trigger: str     # The keyword or risk vector detected
    score: float     # Gravity score or Gate confidence
    details: str     # Refraction offer or summary
    vectors: Optional[Dict[str, float]] = {}

def log_safety_event(event_type: str, trigger: str, score: float, details: str, vectors: Optional[Dict[str, float]] = None):
    """
    Appends a defensive event to the Black Box.
    """
    entry = SafetyEvent(
        timestamp=time.time(),
        readable_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        event_type=event_type,
        trigger=trigger,
        score=score,
        details=details,
        vectors=vectors or {}
    )
    
    # Append to file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")

@router.get("/logs", response_model=List[SafetyEvent])
async def get_audit_logs():
    """
    Returns the last 50 safety interventions.
    Used by the Frontend 'Defense Console'.
    """
    if not LOG_FILE.exists():
        return []
        
    logs = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception:
        return []
    
    # Return newest first
    return list(reversed(logs))[:50]

@router.get("/traces")
async def get_request_traces():
    """
    Returns the full lifecycle history of recent requests.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM request_trace ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("gravity_vectors"):
                try: d["gravity_vectors"] = json.loads(d["gravity_vectors"])
                except: d["gravity_vectors"] = {}
            results.append(d)
        return results
    finally:
        conn.close()
