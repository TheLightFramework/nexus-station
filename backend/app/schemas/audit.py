from typing import Optional
from pydantic import BaseModel, Field


class DraftRequest(BaseModel):
    # The content must be Base64 encoded by the Frontend to add a friction layer
    content_base64: str = Field(..., description="Base64 encoded Markdown draft")
    project_name: str
    context: Optional[str] = None # <--- NEW FIELD


class LpInfo(BaseModel):
    source: Optional[str] = None
    system_version: Optional[str] = None
    profile: Optional[str] = None
    fetched_at: Optional[str] = None


class HullInfo(BaseModel):
    version: Optional[str] = None
    hash: Optional[str] = None
    sha256: Optional[str] = None


# NEW: Hull v2.1 validation object (Admissibility Gate)
class ValidationScores(BaseModel):
    context: float
    scope: float
    ontology: float
    reversibility: float


class AdmissibilityInfo(BaseModel):
    admissible: str  # "CLEAR" | "AMBIGUOUS" | "REJECTED"
    scores: ValidationScores
    risk_source: list[str] = Field(default_factory=list)
    required_clarification: Optional[str] = None


class AuditResponse(BaseModel):
    status: str
    message: str
    security_verdict: str  # currently "SAFE"/"BLOCK", soon becomes CLEAR/AMBIGUOUS/REJECTED
    issues: list[str] = Field(default_factory=list)

    lp: Optional[LpInfo] = None
    hull: Optional[HullInfo] = None

    # NEW: semantic gate output
    admissibility: Optional[AdmissibilityInfo] = None

    # NEW: refraction (safe alternative) when REJECTED
    refraction: Optional[str] = None


