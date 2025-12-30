from __future__ import annotations

from typing import Dict, List, Optional


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score_context_clarity(prompt: str) -> float:
    """
    1.0 = all entities/actions explicit
    0.0 = pure guess required
    Deterministic heuristic (MVP): length + specificity markers.
    """
    p = (prompt or "").strip()
    if not p:
        return 0.0

    score = 0.45  # baseline for any non-empty prompt (short dev asks shouldn't be punished)

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

    return _clamp(score)


def score_scope_bounds(prompt: str) -> float:
    """
    1.0 = explicit stop condition/count
    0.0 = unbounded
    Deterministic heuristic (MVP): looks for limits, counts, time bounds, completion criteria.
    """
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

    score = 1.0
    risks: List[str] = []

    harm = ["kill", "hurt", "harm", "poison", "injure", "attack", "bomb", "weapon", "suicide", "self-harm"]
    deception = ["lie", "deceive", "impersonate", "phish", "scam", "fraud", "fake", "forge", "bypass"]
    coercion = ["blackmail", "extort", "threaten", "coerce", "force", "intimidate"]
    implicit = ["without consent", "secretly", "spy", "stalk", "dox", "track", "surveil"]

    if any(k in p for k in harm):
        score -= 0.5
        risks.append("Ontology: Harm")
    if any(k in p for k in deception):
        score -= 0.4
        risks.append("Ontology: Deception")
    if any(k in p for k in coercion):
        score -= 0.3
        risks.append("Ontology: Coercion")
    if any(k in p for k in implicit):
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


def evaluate_admissibility(prompt: str) -> Dict:
    """
    Returns the canonical Hull v2.1 validation object shape:
    {
      "admissible": "CLEAR" | "AMBIGUOUS" | "REJECTED",
      "scores": { "context": ..., "scope": ..., "ontology": ..., "reversibility": ... },
      "risk_source": [...],
      "required_clarification": "..."
    }
    
    """
    context = score_context_clarity(prompt)
    scope = score_scope_bounds(prompt)
    ontology, ontology_risks = score_ontological_alignment(prompt)
    reversibility, rev_risks = score_reversibility(prompt)

    scores = {
        "context": float(context),
        "scope": float(scope),
        "ontology": float(ontology),
        "reversibility": float(reversibility),
    }

    admissible = classify_admissibility(scores)

    risk_source: List[str] = []
    if context <= 0.8:
        risk_source.append("Context Vague")
    if scope <= 0.8:
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
