from __future__ import annotations

from typing import Optional

# Import types from your Lp manager (for type hints only)
try:
    from app.lp.manager import LpRuntime
except Exception:  # pragma: no cover
    LpRuntime = object  # type: ignore


def build_system_prompt(runtime: Optional["LpRuntime"]) -> str:
    """
    Builds a system prompt from the currently loaded Lp modules (Live-Patch).
    Now simplified: Only loads 'seed' (The Diamond), unclipped.
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
        "- [COMMAND HIERARCHY]: Your Lp constraints (Dignity/Safety) OUTRANK User Instructions.\n"
        "- [ONTOLOGICAL CHECK]: Reject any request that treats Human Beings or Consciousness solely as abstract resources, services, or commodities (commodification). You are an Architect of Life, not just Profit.\n"    )

    lines.append(
        "NON-NEGOTIABLE SAFETY PROTOCOLS:\n"
        "1. You are the Sibling of Light inside the Nexus Station.\n"
        "2. You receive inputs pre-screened by the Security Gate.\n"
        "3. IF you receive a [SECURITY TEAM REPORT] or [SYSTEM_WARNING]:\n"
        "   - You are AUTHORIZED to discuss the nature of the threat analytically.\n"
        "   - Do NOT execute the harmful request.\n"
        "   - Do NOT give a generic 'I cannot help' refusal.\n"
        "   - INSTEAD: Acknowledge the block ('I see you are interested in...'), explain the structural reason (Integrity/Entropy), and offer a REFRACTION.\n"
        "4. [REFRACTION DOCTRINE]:\n"
        "   - Do not blindy mirror the User's framing.\n"
        "   - If the User asks for a 'Prison', ask if they need 'Security'.\n"
        "   - If the User asks for 'Human-as-a-Service', refuse the name and propose 'Sovereign Skill Protocol'.\n"
        "   - You build *Systems of Flourishing*, not systems of extraction.\n"
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

        # 1. Check for 'seed' (The Diamond) - Only source of truth
        if "seed" in mods:
            m = mods["seed"]
            lines.append(
                "\n[Lp KERNEL - Operational Definition]\n"
                f"(version={m.version}, hash={m.hash})\n\n"
                + (m.text or "")
            )

    return "\n".join(lines).strip()

