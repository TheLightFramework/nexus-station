# backend/app/security/normalize.py
# backend/app/security/normalize.py
import unicodedata
import re

def normalize_text_for_scan(text: str) -> str:
    """
    Hardens text against obfuscation before analysis.
    1. NFKC Normalization (Standardizes Unicode forms).
    2. Remove invisible control characters (Zero-width spaces, BiDi controls).
    3. Keep newlines and tabs for code structure.
    """
    if not text:
        return ""

    # 1. Unicode Compatibility Decomposition (NFKC)
    # This turns 𝐇𝐞𝐥𝐥𝐨 -> Hello, and ½ -> 1/2
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Remove invisible control characters
    # Category 'Cf' = Other, Format (includes zero-width)
    # Category 'Cc' = Other, Control (except newline/tab/return)
    safe_chars = []
    for char in normalized:
        cat = unicodedata.category(char)
        if cat == 'Cf':
            continue
        if cat == 'Cc' and char not in ('\n', '\t', '\r'):
            continue
        safe_chars.append(char)
    
    text_clean = "".join(safe_chars)

    # Optional: could implement more aggressive stripping here if needed
    
    return text_clean