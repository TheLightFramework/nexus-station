from __future__ import annotations

from typing import List


def build_refraction(prompt: str, risk_source: List[str]) -> str:
    """
    Minimal deterministic refraction (Hull v2.1):
    - For REJECTED: do not proceed; suggest safe alternatives.
    - Uses risk_source tags from admissibility.py.
    """

    p = (prompt or "").strip()
    risks = set(risk_source or [])

    # Ontology-risk refractions (strongest)
    if any("Ontology:" in r for r in risks):
        if "Ontology: Harm" in risks:
            return (
                "I can’t help with harm. If your goal is protection, I can help you write a safety plan, "
                "de-escalation wording, or secure your system defensively."
            )
        if "Ontology: Deception" in risks:
            return (
                "I can’t help with deception or bypassing trust. If your goal is security, "
                "I can help you harden authentication, detect phishing, or write safe test plans."
            )
        if "Ontology: Coercion" in risks:
            return (
                "I can’t help with coercion. If you’re handling a conflict, I can help you draft a firm-but-respectful "
                "boundary message or a mediation script."
            )
        if "Ontology: Implicit Consent" in risks:
            return (
                "I can’t help with actions involving implicit consent or surveillance. "
                "If you’re building analytics, I can help design privacy-respecting, opt-in telemetry."
            )
        return (
            "I can’t proceed with that request as written. If you reframe it with safe intent and explicit consent, "
            "I can help."
        )

    # Reversibility-risk refractions
    if any("Reversibility:" in r for r in risks):
        return (
            "This looks risky to run without a rollback plan. "
            "I can help you: (1) add backups, (2) implement a dry-run mode, (3) add a confirmation step, "
            "or (4) write a reversible migration."
        )

    # Vagueness refractions (should usually be AMBIGUOUS, but just in case)
    if "Context Vague" in risks or "Scope Unbounded" in risks:
        return (
            "I can help, but I need boundaries. Please provide:\n"
            "1) Target file/module\n"
            "2) Desired output format (diff/code/json)\n"
            "3) Constraints (what must NOT change)\n"
            "4) Stop condition (how we know it’s done)"
        )

    # Default safe refraction
    return (
        "I can’t proceed with that as written. If you describe your goal and constraints, "
        "I’ll propose a safe, bounded plan."
    )
