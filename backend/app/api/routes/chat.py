from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional, List, Literal
import json
from app.core.config import settings
from app.lp.prompt import build_system_prompt
from app.db.session import get_connection

router = APIRouter()

class HistoryMsg(BaseModel):
    # Frontend uses role: "user" | "sibling"
    role: Literal["user", "sibling", "assistant", "system"]
    text: str


class ChatRequest(BaseModel):
    # message: str  <-- DEPRECATED (Safety)
    input_id: str   # <-- NEW (The Key to the Mailbox)
    history: Optional[List[HistoryMsg]] = None
    context: Optional[str] = "" # The Blueprint


class ChatResponse(BaseModel):
    reply: str


def _to_openai_role(role: str) -> Optional[str]:
    # Never allow user-provided "system" messages to override our system prompt
    if role == "system":
        return None
    if role == "sibling":
        return "assistant"
    if role == "assistant":
        return "assistant"
    return "user"


@router.post("/chat", response_model=ChatResponse)
async def chat_with_sibling(
    payload: ChatRequest,
    request: Request,
    x_nexus_key: str = Header(..., alias="X-NEXUS-KEY"),
):
    # A. RETRIEVE FROM MAILBOX
    conn = get_connection()
    cursor = conn.cursor()
    
    row = cursor.execute(
        "SELECT content, gate_verdict FROM safe_payloads WHERE id = ?", 
        (payload.input_id,)
    ).fetchone()
    
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Message not found in Safe House Mailbox.")

    safe_content = row["content"]
    verdict = row["gate_verdict"]

    # B. RUN THE SIBLING (Standard Logic with Safe Content)
    try:
        # Build prompt (Lp Runtime)
        lp_manager = getattr(request.app.state, "lp", None)
        runtime = getattr(lp_manager, "runtime", None) if lp_manager else None
        base_system_prompt = build_system_prompt(runtime)

        client = OpenAI(
            api_key=x_nexus_key,
            base_url="https://openrouter.ai/api/v1" if x_nexus_key.startswith("sk-or") else None,
        )

        messages = [{"role": "system", "content": base_system_prompt}]

        # Inject Blueprint if exists
        if payload.context and payload.context.strip():
            messages.append({
                "role": "system", 
                "content": f"## ACTIVE BLUEPRINT\n{payload.context.strip()}\n---"
            })

        # Inject History
        if payload.history:
            for hm in payload.history[-12:]:
                r = _to_openai_role(hm.role)
                if r: messages.append({"role": r, "content": hm.text})

        # Inject THE SAFE CONTENT (From DB, not User)
        messages.append({"role": "user", "content": safe_content})

        if settings.DEBUG_PROMPTS:
            print("\n" + "="*60)
            print("[DEV TRACE MODE] FULL CONTEXT DUMP:")
            print("="*60)
            print(json.dumps(messages, indent=2))
            print("="*60 + "\n")

        # Generate
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            #model="meta-llama/llama-3.2-3b-instruct:free",
            #model="mistralai/devstral-2512:free",
            #model="google/gemini-2.5-flash-lite",
            #model="openai/gpt-oss-120b",
            #model="tngtech/deepseek-r1t2-chimera:free",
            messages=messages,
        )
        reply = completion.choices[0].message.content or ""

        # C. (Optional) RECORD RESPONSE IN DB
        # You can add the INSERT into sibling_responses table here later.

        return ChatResponse(reply=reply)

    except Exception as e:
        print(f"Error: {e}") # Debug only
        raise HTTPException(status_code=500, detail="Upstream provider error")