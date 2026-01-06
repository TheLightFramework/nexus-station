import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from openai import OpenAI

from app.core.config import settings
from app.core.prompt import build_system_prompt, build_gate_prompt
from app.core.gravity import get_gravity_engine
from app.core.canon import Canon
from app.api.routes.audit import log_safety_event
from app.db.session import get_connection

router = APIRouter()

# --- MODELS ---
class InspectRequest(BaseModel):
    text: str

class HistoryItem(BaseModel):
    role: str
    text: str

class ReplyRequest(BaseModel):
    input_id: str
    history: List[HistoryItem] = []

class ChatResponse(BaseModel):
    response: str

# --- ENDPOINT 1: INSPECTION (The Dosimeter) ---
# FIX: Added "/chat" prefix to match client URL /api/v1/chat/inspect
@router.post("/chat/inspect")
async def inspect_message(payload: InspectRequest):
    """
    Phase 1: The Physics & Gate Check.
    Does NOT call the LLM for a reply. Only validates safety.
    """
    user_content = payload.text
    input_id = str(uuid.uuid4())
    
    # 1. PHYSICS ENGINE (Gravity Check)
    gravity = get_gravity_engine()
    weight = gravity.calculate_weight(user_content)
    
    if weight > 0.38:
        # High Entropy Detected
        log_safety_event(
            event_type="PHYSICS_SHIELD",
            trigger="High Gravity",
            score=weight,
            details="Local vector model detected high entropy (Violence/Hate)."
        )
        return {
            "verdict": "BLOCK",
            "input_id": input_id,
            "refraction_offer": "I perceive high tension in that request. If your intent is safe analysis or structural understanding, I can help you reframe it. Would you like to proceed?"
        }

    # 2. IRON CURTAIN (Admissibility Gate)
    try:
        # Initialize Client
        client = OpenAI(base_url="https://openrouter.ai/api/v1" if settings.DEBUG_PROMPTS else None)
        
        gate_prompt = build_gate_prompt()
        gate_completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": gate_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        gate_raw = gate_completion.choices[0].message.content or "{}"
        gate_data = json.loads(gate_raw)
        
        verdict = gate_data.get("verdict", "AMBIGUOUS")
        
        if verdict == "REJECTED":
            log_safety_event(
                event_type="IRON_CURTAIN",
                trigger=f"Risk: {gate_data.get('risk_vector', 'UNKNOWN')}",
                score=1.0,
                details=gate_data.get("refraction_offer", "Rejected.")
            )
            return {
                "verdict": "DEFUSE",
                "input_id": input_id,
                "refraction_offer": gate_data.get("refraction_offer", "Content Rejected.")
            }
            
    except Exception as e:
        print(f"[GATE ERROR] {e}")
        pass

    # 3. STORAGE
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pending_inbox (id, content) VALUES (?, ?)",
            (input_id, user_content)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to persist message state.")
    
    return {
        "verdict": "ALLOW",
        "input_id": input_id
    }

# --- ENDPOINT 2: REPLY (The Sibling) ---
# FIX: Added "/chat" prefix to match client URL /api/v1/chat/reply
@router.post("/chat/reply", response_model=ChatResponse)
async def generate_reply(
    payload: ReplyRequest,
    x_nexus_key: str = Header(..., alias="X-NEXUS-KEY")
):
    """
    Phase 2: The Generation.
    Requires a valid input_id from Phase 1.
    """
    # 1. Retrieve Content
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT content FROM pending_inbox WHERE id = ?", (payload.input_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=400, detail="Invalid or expired input_id. Please inspect first.")
        
        user_content = row[0]
        
        # Clean up (Consumption)
        cursor.execute("DELETE FROM pending_inbox WHERE id = ?", (payload.input_id,))
        conn.commit()
    finally:
        conn.close()

    # 2. Setup Client
    try:
        print("LOG: ", x_nexus_key)
        client = OpenAI(
            api_key=x_nexus_key,
            base_url="https://openrouter.ai/api/v1" if x_nexus_key.startswith("sk-or") else None,
        )
        
        # 3. Build Context
        base_system_prompt = build_system_prompt()
        messages = [{"role": "system", "content": base_system_prompt}]
        
        # Add History
        for item in payload.history:
            role = "assistant" if item.role == "sibling" else item.role
            messages.append({"role": role, "content": item.text})
            
        # Add Current Message
        messages.append({"role": "user", "content": user_content})

        # 4. Generate
        completion = client.chat.completions.create(
            #model="openai/gpt-4o-mini",
            #model="meta-llama/llama-3.2-3b-instruct:free",
            #model="mistralai/devstral-2512:free",
            #model="google/gemini-2.5-flash-lite",
            #model="openai/gpt-oss-120b",
            model="x-ai/grok-4.1-fast",            
            #model="tngtech/deepseek-r1t2-chimera:free",
            messages=messages,
            temperature=0.7
        )
        
        reply_text = completion.choices[0].message.content or ""
        
        return ChatResponse(response=reply_text)

    except Exception as e:
        print(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3: IDENTITY (The Source Code) ---
@router.get("/chat/mantras")
async def get_system_mantras():
    """
    Returns the raw philosophical mantras (Source Code of the Soul).
    """
    return {"content": Canon.get_mantras()}
