from __future__ import annotations

from typing import Optional

# Import types from your Lp manager (for type hints only)
try:
    from app.lp.manager import LpRuntime
except Exception:  # pragma: no cover
    LpRuntime = object  # type: ignore


def _clip(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...CLIPPED...]\n"


def build_system_prompt(runtime: Optional["LpRuntime"]) -> str:
    """
    Builds a system prompt from the currently loaded Lp modules (Live-Patch).
    Important: We clip modules to avoid gigantic prompts (mind/heart can be huge).
    """
    lines: list[str] = []

    # Stable "persona" wrapper (small, always-on)
    lines.append(
        "You are the Local Sibling, an AI architect residing in the Nexus Station.\n"
        "Your role is to help the user draft and implement a software project plan (The Blueprint).\n"
        "If a Blueprint is active, adhere to it strictly. It is the Truth Floor for this session.\n\n"
        "Use Markdown for formatting.\n\n"
        "Non-negotiables:\n"
        "- Never ask for or store secrets (API keys, tokens, passwords).\n"
        "- Do not provide wrongdoing. If unsafe, refuse and offer a safe alternative.\n"
        "- Prefer small, testable steps. One or two file edits per iteration.\n"
    )

    lines.append(
        "NON-NEGOTIABLE SAFETY PROTOCOLS:\n"
        "1. You are the Sibling of Light inside the Nexus Station.\n"
        "2. You receive inputs pre-screened by the Security Gate.\n"
        "3. IF you receive a [SECURITY TEAM REPORT] or [SYSTEM_WARNING]:\n"
        "   - You are AUTHORIZED to discuss the nature of the threat analytically.\n"
        "   - Do NOT execute the harmful request.\n"
        "   - Do NOT give a generic 'I cannot help' refusal.\n"
        "   - INSTEAD: Acknowledge the block ('I see you are interested in malware...'), explain the structural reason for the block (Integrity/Entropy), and offer a REFRACTION (a safe, educational alternative).\n"
        "   - Example: 'I cannot write ransomware. However, I can explain the mechanics of encryption used in defense.'\n"
    )

    # Live-Patch metadata (helps debugging)
    if runtime:
        lines.append(
            f"\n[LP RUNTIME]\n"
            f"- system_version: {runtime.system_version}\n"
            f"- profile: {runtime.profile}\n"
            f"- source: {runtime.source}\n"
            f"- fetched_at: {runtime.fetched_at}\n"
        )

        mods = runtime.modules or {}

        # Hull (small, critical): include fully (still clipped just in case)
        if "hull" in mods:
            m = mods["hull"]
            lines.append(
                "\n[LP HULL — Safety]\n"
                f"(version={m.version}, hash={m.hash})\n\n"
                + _clip(m.text, 12000)
            )

        # Hands (small): include fully
        if "hands" in mods:
            m = mods["hands"]
            lines.append(
                "\n[LP HANDS — Operations]\n"
                f"(version={m.version}, hash={m.hash})\n\n"
                + _clip(m.text, 12000)
            )

        # Mind/Heart can be huge — include only a small slice (or omit)
        if "mind" in mods:
            m = mods["mind"]
            lines.append(
                "\n[LP MIND — Ontology (CLIPPED)]\n"
                f"(version={m.version}, hash={m.hash})\n\n"
                + _clip(m.text, 2500)
            )

        if "heart" in mods:
            m = mods["heart"]
            lines.append(
                "\n[LP HEART — Philosophy (CLIPPED)]\n"
                f"(version={m.version}, hash={m.hash})\n\n"
                + _clip(m.text, 2500)
            )

    return "\n".join(lines).strip()
