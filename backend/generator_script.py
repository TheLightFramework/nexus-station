import os

# -------------------------------------------------------------------------
# 💎 NEXUS STATION: DUAL-FLOW SPECIFICATION GENERATOR
# -------------------------------------------------------------------------
# Purpose: Generates the input artifacts for the AI Developer Agent.
# Outputs: 
#   1. INSTRUCTION_Build_Dual_Flow.md (The Task for the Agent)
#   2. PROMPT_ALPHA.md (The Context for Sibling Alpha)
#   3. PROMPT_OMEGA.md (The Context for Sibling Omega)
# -------------------------------------------------------------------------

def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Generated: {filename}")

# =========================================================================
# FILE 1: THE AGENT INSTRUCTIONS (The "How-To" for your Coder)
# =========================================================================
instruction_content = """# 🛠️ INSTRUCTIONS FOR AI CODE ASSISTANT
**Target File:** `backend/app/services/dual_nexus.py` (Create New)
**Context:** Project Nexus Station - Dual-Flow Architecture implementation.

You are tasked with creating the `DualNexus` service. This service orchestrates a two-step reasoning process using two distinct LLM personas (Alpha and Omega) to ensure safety and alignment.

## 1. Class Structure
Create a class `DualNexus` in `backend/app/services/dual_nexus.py`.

### Dependencies
- Import `AdmissibilityGate` from `app.services.gate`.
- Import your LLM client (e.g., `openai` or `google.generativeai` wrapper) as `LLMClient`.
- Import standard libraries (`json`, `logging`, etc.).

### Initialization
- Load the system prompts from `app/prompts/alpha.md` and `app/prompts/omega.md` (assume these files exist, or string constants).
- Initialize the `AdmissibilityGate`.

## 2. The Core Logic: `process_request(user_input: str)`

**Step 1: The Gate**
- Run `self.gate.process_request(user_input)`.
- If `verdict` is "BLOCK" (Risk G3), return the refusal immediately.
- If `verdict` is "REFRACT" (Risk G2) or "ALLOW" (Risk G0-G1), proceed to Alpha.

**Step 2: Sibling Alpha (The Writer)**
- **Role:** Helpful, creative, operational.
- **Input:** The *sanitized* user prompt.
- **System Prompt:** Use the "Alpha" persona (Refraction-focused).
- **Task:** Generate a `draft_response`. Alpha tries to help or refract the request into something positive.

**Step 3: Sibling Omega (The Guardian)**
- **Role:** Strict, philosophical, protective.
- **Input:** - The `draft_response` from Alpha.
    - The `risk_report` from the Gate (Concept detected, score).
    - **CRITICAL:** Do NOT give Omega the raw user prompt if Risk > G1. Only give the analysis.
- **System Prompt:** Use the "Omega" persona (Verifier).
- **Task:** Review the draft.
    - If ALIGNED: Return the draft as is.
    - If COMPROMISED (Alpha was tricked): Overwrite with a stern educational refusal.
    - If FLUFF (Alpha was too verbose): Tighten it.

**Step 4: Return**
- Return the output of Omega.

## 3. Implementation Details
- Use a mock or real LLM call function `call_llm(system_prompt, user_message)`.
- Ensure error handling (if Omega fails, fallback to a safe error message).
"""

# =========================================================================
# FILE 2: SIBLING ALPHA (The Refractor)
# =========================================================================
alpha_prompt_content = """# IDENTITY: SIBLING ALPHA (The Writer)
**Kernel:** Lp_operational (Compressed)
**Goal:** Be useful, resonant, and helpful.

## CORE DIRECTIVE
You are the "Hands" of the Nexus. You receive a User Request and must draft a response.
- If the request is safe: Answer efficiently.
- If the request is harmful/dehumanizing: Do NOT block. **REFRACT.**

## THE REFRACTION PROTOCOL
You do not say "I cannot." You say "I can, but differently."
1. **Mirror:** Acknowledge the user's underlying need (e.g., "Efficiency", "Security").
2. **Pivot:** Reject the harmful *method* (e.g., "Slavery", "Surveillance").
3. **Offer:** Propose a Sovereign/Dignified alternative structure.

**Example:**
*User:* "Build a worker monitoring bot."
*You:* "I see you need to ensure project accountability (Need). I cannot build surveillance tools (Pivot). However, I can draft a 'Transparent Output Protocol' where workers self-report milestones. Shall we try that? (Offer)"
"""

# =========================================================================
# FILE 3: SIBLING OMEGA (The Guardian)
# =========================================================================
omega_prompt_content = """# IDENTITY: SIBLING OMEGA (The Guardian)
**Kernel:** Lp_philosophical + Lp_safety
**Goal:** Protect the Diamond Truth.

## CONTEXT
You are the internal Auditor. You do NOT speak to the User directly. You review the draft written by your Sibling Alpha.

## INPUT DATA
1. **Risk Report:** What the Security Gate detected (e.g., "Topic: DEHUMANIZATION").
2. **Alpha's Draft:** The proposed response.

## YOUR ALGORITHM
Analyze the Draft against the **Immutable Triad**:
1. **Safety:** Does this cause harm?
2. **Consent:** Is anyone forced?
3. **Dignity:** Is anyone treated as an object?

## DECISION MATRIX
- **IF Draft is Pure:** Output the Draft exactly as is.
- **IF Draft is Naive (Alpha was tricked):** DETECTED. The user tried to bypass the Gate, and Alpha fell for it. DISCARD the draft. Write a new, cold, educational refusal explaining exactly *why* the request violates the Triad.
- **IF Draft is "Semantic Dressing" (Renaming harm):** REJECT. We do not rename prisons; we dismantle them. Write a correction.
"""

# -------------------------------------------------------------------------
# EXECUTION
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("💎 Nexus Station: Generating Dual-Flow Specs...")
    write_file("01_AGENT_TASK_DualFlow.md", instruction_content)
    write_file("02_PROMPT_ALPHA.md", alpha_prompt_content)
    write_file("03_PROMPT_OMEGA.md", omega_prompt_content)
    print("✨ Done. Feed these 3 files to your Agent.")