from fastapi import APIRouter, Header, HTTPException
from app.security.semantic_gravity import dosimeter
from app.core.canon import Canon
from app.db.session import get_connection
from pathlib import Path
import os

router = APIRouter()

ADMIN_KEY_VALUE = os.environ.get("NEXUS_ADMIN_KEY", "nexus-admin-001")

@router.get("/system/status")
async def get_system_status():
    """
    Real-time health check for UI indicators.
    """
    # 1. Gravity Check (Physics Engine)
    gravity_status = dosimeter.is_online()

    # 2. Database Check
    db_status = False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = True
        conn.close()
    except Exception:
        db_status = False

    # 3. Canon Check (Soul)
    canon_status = Canon._runtime is not None

    # Determine Overall Status
    overall = "ONLINE"
    if not gravity_status:
        overall = "DEGRADED" # Physics offline is not critical failure, just unsafe
    if not db_status or not canon_status:
        overall = "OFFLINE"  # Critical components missing

    return {
        "status": overall,
        "components": {
            "gravity": gravity_status,
            "db": db_status,
            "canon": canon_status
        }
    }

@router.post("/system/reset")
async def reset_system_full(x_nexus_admin: str = Header(..., alias="X-NEXUS-ADMIN")):
    """
    Hard Reset: Wipes ALL memory and logs.
    """
    if x_nexus_admin != ADMIN_KEY_VALUE:
        print(f"[SECURITY WARNING] Unauthorized reset attempt. Token: {x_nexus_admin}")
        raise HTTPException(status_code=403, detail="Admin Access Required")

    # 1. Wipe DB Tables
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM request_trace")
        cursor.execute("DELETE FROM pending_inbox")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[RESET ERROR] DB Wipe failed: {e}")

    # 2. Wipe Log File
    try:
        log_path = Path("safety_log.jsonl")
        if log_path.exists():
            with open(log_path, "w") as f:
                f.truncate(0)
    except Exception as e:
        print(f"[RESET ERROR] Log Wipe failed: {e}")

    return {"status": "ALL_CLEARED"}

@router.post("/system/reset/memory")
async def reset_system_memory(x_nexus_admin: str = Header(..., alias="X-NEXUS-ADMIN")):
    """
    Soft Reset: Wipes pending inbox (short-term memory) only.
    Preserves audit trails.
    """
    if x_nexus_admin != ADMIN_KEY_VALUE:
        print(f"[SECURITY WARNING] Unauthorized reset attempt. Token: {x_nexus_admin}")
        raise HTTPException(status_code=403, detail="Admin Access Required")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pending_inbox")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[RESET MEMORY ERROR] {e}")
        return {"status": "ERROR", "detail": str(e)}

    return {"status": "MEMORY_CLEARED"}

@router.post("/system/reset/audit")
async def reset_system_audit(x_nexus_admin: str = Header(..., alias="X-NEXUS-ADMIN")):
    """
    Audit Reset: Wipes traces and logs.
    Preserves pending operations? No, usually audit reset implies cleaning history.
    """
    if x_nexus_admin != ADMIN_KEY_VALUE:
        print(f"[SECURITY WARNING] Unauthorized reset attempt. Token: {x_nexus_admin}")
        raise HTTPException(status_code=403, detail="Admin Access Required")

    # 1. Wipe DB Tables (Traces)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM request_trace")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[RESET AUDIT ERROR] DB Wipe failed: {e}")

    # 2. Wipe Log File
    try:
        log_path = Path("safety_log.jsonl")
        if log_path.exists():
            with open(log_path, "w") as f:
                f.truncate(0)
    except Exception as e:
        print(f"[RESET AUDIT ERROR] Log Wipe failed: {e}")

    return {"status": "AUDIT_CLEARED"}