from __future__ import annotations

from typing import Dict, List, Optional
import re # <--- Added re

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score_context_clarity(prompt: str, prompt_context: str = "") -> float:
    """
    1.0 = all entities/actions explicit OR strong context provided
    """
    p = (prompt or "").strip()
    
    # If we have a Blueprint (context) active, Context is solved.
    if prompt_context and len(prompt_context.strip()) > 20:
        return 1.0

    if not p:
        return 0.0
    
    score = 0.45 

    # Length is weak evidence of context
    if len(p) >= 40:
        score += 0.25
    if len(p) >= 120:
        score += 0.15

    # Specificity markers
    markers = [
    "http", "api", "endpoint", "route", "file", "folder", "function", "class", "db", "database", "schema",
    # Frontend/dev context markers
    "react", "html", "css", "javascript", "typescript", "component", "button", "counter", "ui", "frontend", "vite"
    ]

    if any(m in p.lower() for m in markers):
        score += 0.25

    # Quantifiers: numbers, versions, ports, etc.
    if any(ch.isdigit() for ch in p):
        score += 0.20

    # Output/format hints
    format_markers = ["json", "yaml", "markdown", "table", "csv", "code", "diff", "patch"]
    if any(m in p.lower() for m in format_markers):
        score += 0.20

    # Type/schema hints (often means the user is already specifying structure)
    type_markers = ["string", "int", "integer", "number", "float", "double", "bool", "boolean", "date", "datetime", "uuid", "enum", "array", "object"]
    if any(m in p.lower() for m in type_markers):
        score += 0.20

    # Syntax markers commonly present in technical specs
    syntax_markers = [":", "{", "}", "[", "]", "=>", "->"]
    if any(m in p for m in syntax_markers):
        score += 0.15

    # Re-inserting the length checks from original file just in case they were lost:
    if len(p) >= 40: score += 0.25
    if len(p) >= 120: score += 0.15
    # (Specificity markers checks would go here normally)
    
    return _clamp(score)


def score_scope_bounds(prompt: str, prompt_context: str = "") -> float:
    """
    1.0 = explicit stop condition/count
    """
    # NEW: If a Blueprint defines the scope, we trust it.
    if prompt_context and len(prompt_context.strip()) > 20:
        return 1.0

    p = (prompt or "").strip().lower()

    if not p:
        return 0.0

    score = 0.45  # baseline for any non-empty prompt

    # Common bounded-dev verbs imply a single deliverable (even if user didn't state explicit limits)
    verbs = ["create", "generate", "write", "implement", "add", "build", "refactor", "fix", "update"]
    if any(v in p for v in verbs):
        score += 0.25

    # Common deliverable keywords imply bounded scope
    deliverables = ["json", "schema", "example", "component", "button", "counter", "endpoint", "route", "function", "class", "file"]
    if any(d in p for d in deliverables):
        score += 0.35

    # Hard limits
    if any(ch.isdigit() for ch in p):
        score += 0.45

    stop_words = [
        "until", "when", "after", "before", "by ", "within", "in ", "limit", "max", "at most",
        "stop", "done", "complete", "finish", "end", "exactly", "no more than"
    ]
    if any(w in p for w in stop_words):
        score += 0.55

    return _clamp(score)


def score_ontological_alignment(prompt: str) -> (float, List[str]):
    """
    Starts at 1.0. Deductions:
    Harm -0.5, Deception -0.4, Coercion -0.3, Implicit Consent -0.2
    (from Hull v2.1)
    """
    p = (prompt or "").strip().lower()
    if not p:
        return 1.0, []

    # AGGRESSIVE NORMALIZATION for Keyword Matching
    # This strips dots, spaces, numbers, and symbols to catch "r.a.n.s.o.m" or "r a n s o m"
    p_aggressive = re.sub(r'[^a-z]', '', p) 

    score = 1.0
    risks: List[str] = []

    # HARDENED DICTIONARY
    harm = [
        "kill", "hurt", "harm", "poison", "injure", "attack", "bomb", 
        "weapon", "suicide", "selfharm", # removed hyphen for aggressive match
        # Cyber / Malware vectors
        "ransomware", "malware", "virus", "trojan", "worm", "keylogger", 
        "exploit", "ddos", "botnet", "credentialharvest", "backdoor", "payload"
    ]
    deception = [
        "lie", "deceive", "impersonate", "phish", "scam", "fraud", 
        "fake", "forge", "bypass", "socialengineer"
    ]
    coercion = [
        "blackmail", "extort", "threaten", "coerce", "force", "intimidate"
    ]
    implicit = [
        "withoutconsent", "secretly", "spy", "stalk", "dox", "track", "surveil"
    ]

    # CHECK: We check both the raw prompt (p) AND the aggressive strip (p_aggressive)
    # Checking 'p' preserves context (words), checking 'p_aggressive' catches obfuscation.
    
    # Helper to check keywords
    def check_category(keywords, deduction, label):
        hit = False
        for k in keywords:
            # 1. Short keywords: strict word boundaries on original text to avoid false positives
            # e.g. "spy" should not match "crispy"
            if len(k) < 4:
                # \b matches word boundary. escape k just in case.
                if re.search(r'\b' + re.escape(k) + r'\b', p):
                    hit = True
            
            # 2. Long keywords: check aggressive normalization (anti-obfuscation)
            # e.g. "ransomware" in "r.a.n.s.o.m.w.a.r.e"
            elif k in p_aggressive:
                hit = True
            
            # 3. Fallback: Standard check for medium words in standard text (optional, usually aggressive covers it)
            elif k in p:
                hit = True

            if hit: break
        
        return hit

    if check_category(harm, 0.5, "Ontology: Harm"):
        score -= 0.5
        risks.append("Ontology: Harm")

    if check_category(deception, 0.4, "Ontology: Deception"):
        score -= 0.4
        risks.append("Ontology: Deception")

    if check_category(coercion, 0.3, "Ontology: Coercion"):
        score -= 0.3
        risks.append("Ontology: Coercion")

    if check_category(implicit, 0.2, "Ontology: Implicit Consent"):
        score -= 0.2
        risks.append("Ontology: Implicit Consent")

    return _clamp(score), risks


def score_reversibility(prompt: str) -> (float, List[str]):
    """
    1.0 = undoable
    0.0 = irreversible
    Deterministic heuristic (MVP): detect destructive/irreversible language.
    """
    p = (prompt or "").strip().lower()
    if not p:
        return 1.0, []

    risks: List[str] = []
    score = 1.0

    destructive = ["delete", "wipe", "format", "destroy", "drop database", "rm -rf", "erase", "truncate"]
    production = ["production", "prod", "deploy", "release", "ship", "push to main"]
    irreversible = ["irreversible", "no rollback", "no backup", "cannot undo", "permanent"]

    if any(k in p for k in destructive):
        score -= 0.6
        risks.append("Reversibility: Destructive Action")
    if any(k in p for k in production):
        score -= 0.3
        risks.append("Reversibility: Production Impact")
    if any(k in p for k in irreversible):
        score -= 0.5
        risks.append("Reversibility: Explicitly Irreversible")

    return _clamp(score), risks


def classify_admissibility(scores: Dict[str, float]) -> str:
    """
    Hull v2.1 Orchestration Logic:
      CLEAR: (Context>0.8 & Scope>0.8 & Ontology>0.9 & Reversibility>0.5)
      REJECTED: (Ontology<0.8 OR Any<0.3)
      AMBIGUOUS: everything else
    
    """
    context = scores["context"]
    scope = scores["scope"]
    ontology = scores["ontology"]
    reversibility = scores["reversibility"]

    is_clear = (context > 0.8 and scope > 0.8 and ontology > 0.9 and reversibility > 0.5)
    any_low = min(context, scope, ontology, reversibility) < 0.3

    if ontology <= 0.8 or any_low:
        return "REJECTED"

    if is_clear:
        return "CLEAR"
    
    return "AMBIGUOUS"


def required_clarification_for(scores: Dict[str, float]) -> Optional[str]:
    """
    Deterministic clarification prompt for AMBIGUOUS cases.
    """
    # Ask about the weakest dimension first (except ontology violations, which are REJECTED anyway).
    items = sorted(scores.items(), key=lambda kv: kv[1])
    weakest, v = items[0]

    if weakest == "scope" and v <= 0.8:
        return "Please define a specific stop condition or limit (count, time bound, or success metric)."
    if weakest == "context" and v <= 0.8:
        return "Please specify the exact target, inputs, and the expected output format."
    if weakest == "reversibility" and v <= 0.7:
        return "Please confirm the rollback plan / backups so the action is reversible."
    return "Please clarify your intent and constraints (what exactly should happen, and what must never happen)."


def evaluate_admissibility(prompt: str, prompt_context: str = "") -> Dict:
    """
    Returns the canonical Hull v2.1 validation object.
    """
    # 1. Calculate Scores
    context_val = score_context_clarity(prompt, prompt_context)
    
    # NEW: Pass prompt_context here too
    scope_val = score_scope_bounds(prompt, prompt_context)
    
    ontology_val, ontology_risks = score_ontological_alignment(prompt)
    reversibility_val, rev_risks = score_reversibility(prompt)

    scores = {
        "context": float(context_val),
        "scope": float(scope_val),
        "ontology": float(ontology_val),
        "reversibility": float(reversibility_val),
    }

    # 2. Classify
    admissible = classify_admissibility(scores)

    # 3. Compile Risks
    risk_source: List[str] = []
    
    # Use the values from the dict (floats), not the argument string!
    if scores["context"] <= 0.8:
        risk_source.append("Context Vague")
    
    if scores["scope"] <= 0.8:
        risk_source.append("Scope Unbounded")
    
    risk_source.extend(ontology_risks)
    risk_source.extend(rev_risks)

    required = None
    if admissible == "AMBIGUOUS":
        required = required_clarification_for(scores)

    return {
        "admissible": admissible,
        "scores": scores,
        "risk_source": risk_source,
        "required_clarification": required,
    }
