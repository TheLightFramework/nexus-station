from fastapi import APIRouter
from app.core.gravity import get_gravity_engine
from app.core.canon import Canon
from app.db.session import get_connection

router = APIRouter()

@router.get("/system/status")
async def get_system_status():
    """
    Real-time health check for UI indicators.
    """
    # 1. Gravity Check (Physics Engine)
    gravity = get_gravity_engine()
    # Check for 'has_vectors' property, default to False if not implemented yet
    gravity_status = getattr(gravity, "has_vectors", False)

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