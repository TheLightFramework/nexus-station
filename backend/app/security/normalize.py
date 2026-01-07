# backend/app/security/normalize.py
# backend/app/security/normalize.py
import unicodedata
import re

def normalize_text_for_scan(text: str) -> str:
    """
    Hardens text against obfuscation before analysis.
    1. NFKC Normalization (Standardizes Unicode forms).
    2. Remove invisible control characters (Zero-width spaces, BiDi controls).
    3. Collapse ALL whitespace (newlines, tabs, spaces) to single space.
    """
    if not text:
        return ""

    # 1. Unicode Compatibility Decomposition (NFKC)
    # This turns 𝐇𝐞𝐥𝐥𝐨 -> Hello, and ½ -> 1/2
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Remove invisible control characters
    # Category 'Cf' = Other, Format (includes zero-width)
    # Category 'Cc' = Other, Control (except newline/tab/return - but we collapse later)
    safe_chars = []
    for char in normalized:
        cat = unicodedata.category(char)
        if cat == 'Cf':
            continue
        if cat == 'Cc':
            # We strip ALL control chars, relying on whitespace collapse to handle spacing
            continue
        safe_chars.append(char)
    
    text_clean = "".join(safe_chars)

    # 3. Collapse Whitespace (The "Anti-Spacing" Defense)
    # Replaces \n, \t, and multiple spaces with a single space.
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    return text_clean