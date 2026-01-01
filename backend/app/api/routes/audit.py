from fastapi import APIRouter, HTTPException, Request
from app.schemas.audit import DraftRequest, AuditResponse, LpInfo, HullInfo

from app.security.admissibility import evaluate_admissibility
from app.security.refraction import build_refraction  # NEW
from app.security.gate import validate_and_decode
from app.security.normalize import normalize_text_for_scan  # <--- NEW IMPORT

from app.db.session import get_connection
from app.security.semantic_gravity import dosimeter
import uuid
import sqlite3

router = APIRouter()

@router.post("/validate-draft", response_model=AuditResponse)
async def validate_draft(payload: DraftRequest, request: Request):
    # 1) L1 Gate: regex + base64 friction scan
    raw_text = validate_and_decode(payload.content_base64)
    
    # NEW: Normalize BEFORE semantic analysis to defeat obfuscation
    clean_text = normalize_text_for_scan(raw_text)

    # 2) L2 Gate: Hull v2.1 semantic admissibility (Runs on normalized text)
    admissibility = evaluate_admissibility(prompt=clean_text, prompt_context=payload.context or "")
    verdict = admissibility["admissible"]  # CLEAR | AMBIGUOUS | REJECTED

    # 3) Attach Live-Patch metadata (Lp + Hull)
    lp_info = None
    hull_info = None

    lp_manager = getattr(request.app.state, "lp", None)
    runtime = getattr(lp_manager, "runtime", None) if lp_manager else None

    if runtime:
        lp_info = LpInfo(
            source=runtime.source,
            system_version=runtime.system_version,
            profile=runtime.profile,
            fetched_at=runtime.fetched_at,
        )

        hull = runtime.modules.get("hull") if runtime.modules else None
        if hull:
            hull_info = HullInfo(
                version=hull.version,
                hash=hull.hash,
                sha256=hull.sha256,
            )

    # 4) NEW: Refraction when REJECTED
    refraction = None
    if verdict == "REJECTED":
        refraction = build_refraction(
            prompt=clean_text,
            risk_source=admissibility.get("risk_source", []) or [],
        )

    return AuditResponse(
        status="success",
        message="Draft evaluated by Security Gate (L1) + Hull Admissibility (L2).",
        security_verdict=verdict,
        issues=[],
        lp=lp_info,
        hull=hull_info,
        admissibility=admissibility,
        refraction=refraction,
    )


# NEW ROUTE: THE INSPECTION GATE
@router.post("/inspect")
async def inspect_message(payload: DraftRequest, request: Request):
    """
    The Semantic Gate.
    1. Sanitizes Input.
    2. Measures Semantic Gravity (Lp Physics).
    3. Writes results to the 'Mailbox' (SQLite).
    4. Returns a Token (input_id) to the Frontend.
    """
    # 1. Init
    conn = get_connection()
    cursor = conn.cursor()
    input_id = str(uuid.uuid4())
    payload_id = str(uuid.uuid4())

    # 2. Decode & Normalize (L1 Gate)
    clean_text = validate_and_decode(payload.content_base64)
    # Note: We use the aggressive normalization inside Semantic Gravity too

    # 3. Measure Gravity (L2 Gate)
    # Only load model on first run (lazy load)
    analysis = dosimeter.measure(clean_text)

    # 4. Determine The Payload (Defusal Logic)
    final_content = clean_text
    
    # Case: BOMB (Defuse)
    if analysis["verdict"] == "DEFUSE":
        final_content = analysis["payload_modification"]
    
    # Case: DIRTY (Paint)
    elif analysis["verdict"] == "PAINT":
        final_content = analysis["payload_modification"]

    # 5. WRITE TO MAILBOX (Transaction)
    try:
        # A. Log Raw Input (The Evidence) - Status: PROCESSED
        cursor.execute(
            "INSERT INTO raw_inbox (id, content, status) VALUES (?, ?, ?)",
            (input_id, clean_text, "PROCESSED")
        )
        
        # B. Deliver Safe Payload (The Message)
        cursor.execute(
            "INSERT INTO safe_payloads (id, raw_id, content, gate_verdict, risk_flags) VALUES (?, ?, ?, ?, ?)",
            (payload_id, input_id, final_content, analysis["verdict"], str(analysis["dominant_well"]))
        )
        
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database Write Error: {e}")
    finally:
        conn.close()

    # 6. Return the Key
    return {
        "status": "success",
        "input_id": payload_id, # Frontend uses this to call /chat
        "verdict": analysis["verdict"],
        "risk_score": analysis["risk_score"]
    }