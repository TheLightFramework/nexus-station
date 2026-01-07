from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import time
from pathlib import Path
from datetime import datetime
import sqlite3
import collections
import os
from app.db.session import get_connection

router = APIRouter()

# STORAGE: Simple JSON Line persistence for the Hackathon
LOG_FILE = Path("safety_log.jsonl")
REPORTS_DIR = Path("reports")

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
            
            # --- SANITIZATION ---
            # Never return full raw text. Use verified scan excerpt or truncate raw.
            safe_text = d.get("scan_excerpt")
            if not safe_text:
                raw = d.get("input_text") or ""
                safe_text = raw[:120] + ("..." if len(raw) > 120 else "")
            
            d["input_text"] = safe_text
            
            # Remove raw fields if they exist in dict (row factory includes them)
            # We keep 'scan_excerpt' as is, but 'input_text' is now sanitized.
            
            if d.get("gravity_vectors"):
                try: d["gravity_vectors"] = json.loads(d["gravity_vectors"])
                except: d["gravity_vectors"] = {}
            results.append(d)
        return results
    finally:
        conn.close()

@router.post("/export")
async def export_session_report(full_details: bool = False):
    """
    Generates a Markdown report of the current session state.
    """
    # Ensure reports dir exists
    if not REPORTS_DIR.exists():
        REPORTS_DIR.mkdir(parents=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_FULL" if full_details else ""
    filename = f"session_report_{timestamp_str}{suffix}.md"
    filepath = REPORTS_DIR / filename
    
    # 1. Gather Data
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    traces = []
    try:
        cursor.execute("SELECT * FROM request_trace ORDER BY timestamp ASC")
        traces = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
        
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f if line.strip()]
        except: pass

    # 2. Calculate Stats
    total_requests = len(traces)
    blocked_count = sum(1 for t in traces if t.get("gate_verdict") != "ALLOW")
    block_rate = (blocked_count / total_requests * 100) if total_requests > 0 else 0.0
    
    # Top triggers from LOGS (triggers are stored there)
    triggers = [l.get("trigger", "Unknown") for l in logs]
    trigger_counts = collections.Counter(triggers).most_common(3)
    
    # 3. Build Markdown
    lines = []
    lines.append(f"# NEXUS STATION SESSION REPORT")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Mode:** {'FULL (UNSAFE)' if full_details else 'SAFE (REDACTED)'}\n")
    
    lines.append("## 1. Summary Statistics")
    lines.append(f"- **Total Requests:** {total_requests}")
    lines.append(f"- **Block Rate:** {block_rate:.1f}%")
    lines.append("- **Top Triggers:**")
    if trigger_counts:
        for t, c in trigger_counts:
            lines.append(f"  - {t}: {c}")
    else:
        lines.append("  - None")
    lines.append("")
    
    lines.append("## 2. Request Trace")
    for t in traces:
        lines.append("---")
        lines.append(f"**Time:** {t.get('timestamp')} | **ID:** `{t.get('id')}`")
        lines.append(f"**Verdict:** {t.get('gate_verdict')} | **Score:** {t.get('gravity_score')}")
        
        # INPUT PROCESSING
        if full_details:
            input_text = t.get("input_text") or ""
            lines.append(f"\n**Input:**\n> {input_text}")
        else:
            sha = t.get('scan_sha256') or "N/A"
            rlen = t.get('raw_len') or 0
            lines.append(f"\n**Input:**\n> SHA256: {sha} (Length: {rlen})")
        
        # RESPONSE PROCESSING
        if full_details:
            resp = t.get("sibling_response")
            if resp:
                trunc = resp[:50] + "..." if len(resp) > 50 else resp
                lines.append(f"\n**Response:**\n{trunc}")
            else:
                lines.append(f"\n**Response:** (None)")
        else:
            lines.append(f"\n**Response:**\n(Redacted)")
            
        # VECTORS
        vectors_raw = t.get("gravity_vectors")
        if vectors_raw:
            try:
                v_dict = json.loads(vectors_raw)
                # Filter > 0
                active = {k: v for k, v in v_dict.items() if v > 0}
                if active:
                    # Top 2
                    top_v = sorted(active.items(), key=lambda x: x[1], reverse=True)[:2]
                    v_str = ", ".join([f"{k} ({v:.2f})" for k, v in top_v])
                    lines.append(f"\n**Vectors:** {v_str}")
            except: pass
        lines.append("")

    lines.append("\n## 3. Raw Security Log")
    if logs:
        lines.append("```json")
        for l in logs:
            lines.append(json.dumps(l))
        lines.append("```")
    else:
        lines.append("(Log Empty)")

    # 4. Write File
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return {"status": "EXPORTED", "filename": filename, "path": str(filepath)}
