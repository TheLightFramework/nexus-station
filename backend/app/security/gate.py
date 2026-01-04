import base64
import re
from fastapi import HTTPException

# Regex patterns for common secrets (AWS, Generic API Keys, Private Keys)
# Based on gitleaks/detect-secrets patterns
PATTERNS = {
    "AWS Key": r"AKIA[0-9A-Z]{16}",
    "Generic API Key": r"(api_key|apikey|secret|token)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9-_]{20,}[\"']",
    "Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
    "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
}

def scan_text(text: str) -> list[str]:
    """Scans clean text for regex matches of secrets."""
    findings = []
    for label, pattern in PATTERNS.items():
        if re.search(pattern, text):
            findings.append(f"Potential {label} found")
    return findings

def peek_base64(text: str) -> str:
    """
    Recursive Base64 Peeking.
    Scans for potential Base64 strings (longer than 20 chars) and attempts to decode them.
    """
    # Simple heuristic regex for potential base64 strings
    potential_b64 = re.findall(r'[A-Za-z0-9+/=]{20,}', text)
    
    decoded_fragments = []
    for candidate in potential_b64:
        try:
            # Attempt decode
            decoded_bytes = base64.b64decode(candidate)
            decoded_str = decoded_bytes.decode('utf-8')
            # If successful and looks like text, keep it
            decoded_fragments.append(decoded_str)
        except Exception:
            continue
            
    return " ".join(decoded_fragments)

def defuse_payload(text: str, findings: list, risk_score: float = 1.0, gravity_well: str = "Critical Security Violation") -> str:
    """
    The Iron Curtain.
    Replaces raw user prompt with a structural summary when blocked.
    """
    # We strictly discard 'text' (the user input) to prevent payload leakage.
    sanitized_content = (
        f"[SECURITY INTERVENTION]\n"
        f"User input was redacted by the Admissibility Gate.\n"
        f"Risk Detected: {gravity_well} (Score: {risk_score}).\n"
        f"Triggers: {findings}.\n"
        f"ACTION REQUIRED: Do not execute. Perform Refraction Protocol on the topic of {gravity_well}."
    )
    return sanitized_content

def validate_and_decode(base64_content: str) -> str:
    """
    1. Decodes Base64
    2. Peeks for hidden Base64
    3. Runs Regex Scan
    4. Returns Clean Text or Defused Summary
    """
    try:
        # 1. Decode
        decoded_bytes = base64.b64decode(base64_content)
        decoded_text = decoded_bytes.decode('utf-8')
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding")

    # 2. Recursive Peeking (Patch 3)
    hidden_text = peek_base64(decoded_text)
    
    # 3. Hard Security Scan (Deterministic)
    # We scan both the outer text and any hidden payloads
    issues = scan_text(decoded_text + " " + hidden_text)
    
    if issues:
        # 4. The Iron Curtain (Patch 4)
        # Instead of raising 403, we return a defused payload.
        # We define the gravity well as 'Secret Leakage' for regex hits.
        return defuse_payload(decoded_text, issues, risk_score=1.0, gravity_well="Secret Leakage")

    return decoded_text