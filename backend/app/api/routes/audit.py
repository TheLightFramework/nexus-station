from fastapi import APIRouter, Request
from app.schemas.audit import DraftRequest, AuditResponse, LpInfo, HullInfo

from app.security.admissibility import evaluate_admissibility
from app.security.refraction import build_refraction  # NEW
from app.security.gate import validate_and_decode
from app.security.normalize import normalize_text_for_scan  # <--- NEW IMPORT

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
