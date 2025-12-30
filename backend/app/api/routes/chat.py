from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional, List, Literal
from app.lp.prompt import build_system_prompt

router = APIRouter()

class HistoryMsg(BaseModel):
    # Frontend uses role: "user" | "sibling"
    role: Literal["user", "sibling", "assistant", "system"]
    text: str


class ChatRequest(BaseModel):
    message: str
    # Backward compat: old field (unused for now)
    context: Optional[str] = ""
    # New: conversation history (optional)
    history: Optional[List[HistoryMsg]] = None


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


def _clip_text(s: str, max_chars: int = 4000) -> str:
    if not s:
        return ""
    return s if len(s) <= max_chars else s[:max_chars] + "\n[...CLIPPED...]"


@router.post("/chat", response_model=ChatResponse)
async def chat_with_sibling(
    payload: ChatRequest,
    request: Request,
    x_nexus_key: str = Header(..., alias="X-NEXUS-KEY"),
):
    try:
        # Build system prompt from Live-Patch runtime
        lp_manager = getattr(request.app.state, "lp", None)
        runtime = getattr(lp_manager, "runtime", None) if lp_manager else None
        
        base_system_prompt = build_system_prompt(runtime)

        # Init provider client
        client = OpenAI(
            api_key=x_nexus_key,
            base_url="https://openrouter.ai/api/v1" if x_nexus_key.startswith("sk-or") else None,
        )

        messages = [{"role": "system", "content": base_system_prompt}]

        # NEW: Inject Blueprint/Context if it exists
        if payload.context and payload.context.strip():
            blueprint_injection = (
                "## ACTIVE BLUEPRINT / CONTEXT\n"
                "The user has pinned the following structure. Use this as your reference architecture. "
                "Do not deviate from these constraints unless explicitly requested.\n\n"
                f"{payload.context.strip()}\n\n"
                "---"
            )
            messages.append({"role": "system", "content": blueprint_injection})

        # History injection
        if payload.history:
            # Keep last 12 items to manage tokens, preserving recent context
            for hm in payload.history[-12:]:
                r = _to_openai_role(hm.role)
                if not r: 
                    continue
                messages.append({"role": r, "content": _clip_text(hm.text)})

        # Current user message
        messages.append({"role": "user", "content": _clip_text(payload.message)})

        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini", # Ideally dynamic later, but good for MVP
            messages=messages,
        )

        reply = completion.choices[0].message.content or ""
        return ChatResponse(reply=reply)

    except Exception as e:
        # Zero-log policy enforcement happens here implicitly via logging.py filter
        # But we ensure we don't leak details in the 500 response
        raise HTTPException(status_code=500, detail="Upstream provider error or connection failure")