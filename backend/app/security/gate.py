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

def validate_and_decode(base64_content: str) -> str:
    """
    1. Decodes Base64
    2. Runs Regex Scan
    3. Returns Clean Text or Raises 400
    """
    try:
        # 1. Decode
        decoded_bytes = base64.b64decode(base64_content)
        decoded_text = decoded_bytes.decode('utf-8')
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding")

    # 2. Hard Security Scan (Deterministic)
    issues = scan_text(decoded_text)
    
    if issues:
        # BLOCK THE REQUEST. Do not log the content.
        raise HTTPException(
            status_code=403, 
            detail={
                "error": "Security Gate Triggered", 
                "issues": issues,
                "message": "Remove secrets/emails from draft before submitting."
            }
        )

    return decoded_text