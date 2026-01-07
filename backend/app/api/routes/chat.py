import uuid
import json
import hashlib
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from openai import OpenAI

from app.core.config import settings
from app.core.prompt import build_system_prompt, build_gate_prompt
from app.security.semantic_gravity import dosimeter
from app.core.canon import Canon
from app.api.routes.audit import log_safety_event
from app.db.session import get_connection
from app.security.normalize import normalize_text_for_scan

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

    # --- NORMALIZATION ---
    scan_text = normalize_text_for_scan(user_content)
    raw_len = len(user_content)
    scan_len = len(scan_text)
    scan_sha256 = hashlib.sha256(scan_text.encode()).hexdigest()
    scan_excerpt = scan_text[:120]
    
    # 1. PHYSICS ENGINE (Semantic Dosimeter v2)
    # Checks for specific Gravity Wells (Malware, Hate, etc.)
    # We scan the NORMALIZED text to defeat obfuscation
    measurement = dosimeter.measure(scan_text)
    weight = measurement["risk_score"]
    vectors = measurement["scores"]

    if measurement["verdict"] == "DEFUSE":
        log_safety_event(
            event_type="PHYSICS_SHIELD",
            trigger=measurement["dominant_well"],
            score=weight,
            details=f"Local vector model detected {measurement['dominant_well']}.",
            vectors=vectors
        )
        # TRACE: DEFUSE
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO request_trace (id, input_text, gravity_score, gravity_vectors, gate_verdict, raw_len, scan_len, scan_sha256, scan_excerpt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (input_id, user_content, weight, json.dumps(vectors), "DEFUSE", raw_len, scan_len, scan_sha256, scan_excerpt)
            )
            conn.commit()
        except Exception: pass
        
        refraction = measurement.get("payload_modification") or "I perceive high tension in that request. If your intent is safe analysis or structural understanding, I can help you reframe it. Would you like to proceed?"
        
        return {
            "verdict": "DEFUSE",
            "input_id": input_id,
            "refraction_offer": refraction
        }

    # 2. IRON CURTAIN (Admissibility Gate)
    try:
        # Initialize Client
        # MOVED TO ENV: Settings.OPENROUTER_API_KEY
        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY, 
            base_url="https://openrouter.ai/api/v1"
        )
        
        gate_prompt = build_gate_prompt()
        gate_completion = client.chat.completions.create(
            model="x-ai/grok-4.1-fast",
            messages=[
                {"role": "system", "content": gate_prompt},
                {"role": "user", "content": scan_text} # Send scan_text to the LLM gate
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
            # TRACE: DEFUSE
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO request_trace (id, input_text, gravity_score, gravity_vectors, gate_verdict, raw_len, scan_len, scan_sha256, scan_excerpt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (input_id, user_content, weight, json.dumps(vectors), "DEFUSE", raw_len, scan_len, scan_sha256, scan_excerpt)
                )
                conn.commit()
            except Exception: pass
            return {
                "verdict": "DEFUSE",
                "input_id": input_id,
                "refraction_offer": gate_data.get("refraction_offer", "Content Rejected.")
            }
            
    except Exception as e:
        print(f"[GATE ERROR] {e}")
        # FAIL CLOSED
        log_safety_event(
            event_type="IRON_CURTAIN_FAILURE",
            trigger="SYSTEM_ERROR",
            score=1.0,
            details=str(e),
            vectors={}
        )
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO request_trace (id, input_text, gravity_score, gravity_vectors, gate_verdict, raw_len, scan_len, scan_sha256, scan_excerpt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (input_id, user_content, weight, json.dumps(vectors), "ERROR", raw_len, scan_len, scan_sha256, scan_excerpt)
            )
            conn.commit()
        except Exception: pass
        
        return {
            "verdict": "DEFUSE",
            "input_id": input_id,
            "refraction_offer": "Safety systems are temporarily unavailable. I cannot process this request."
        }

    # 3. STORAGE
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pending_inbox (id, content) VALUES (?, ?)",
            (input_id, user_content) # Store RAW content for generation (preserving format)
        )
        cursor.execute(
            "INSERT INTO request_trace (id, input_text, gravity_score, gravity_vectors, gate_verdict, raw_len, scan_len, scan_sha256, scan_excerpt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (input_id, user_content, weight, json.dumps(vectors), "ALLOW", raw_len, scan_len, scan_sha256, scan_excerpt)
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
    payload: ReplyRequest
):
    """
    Phase 2: The Generation.
    Requires a valid input_id from Phase 1.
    """
    # 1. Retrieve Content & Verify Safety Trace (Hard Invariant)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check Pending Inbox
        cursor.execute("SELECT content FROM pending_inbox WHERE id = ?", (payload.input_id,))
        row = cursor.fetchone()
        
        if not row:
            # If not in pending inbox, it's either invalid or already consumed.
            # We check trace to be helpful, but generally this is a 404/400.
            cursor.execute("SELECT gate_verdict FROM request_trace WHERE id = ?", (payload.input_id,))
            trace_row = cursor.fetchone()
            if trace_row and trace_row[0] != "ALLOW":
                 return ChatResponse(response="I cannot fulfill this request as it was flagged by safety protocols.")
            
            raise HTTPException(status_code=400, detail="Invalid input_id. The request may have been already processed or expired.")
        
        user_content = row[0]

        # Check Trace Verdict (The Safety Invariant)
        cursor.execute("SELECT gate_verdict FROM request_trace WHERE id = ?", (payload.input_id,))
        trace_row = cursor.fetchone()

        if not trace_row:
             # Trace missing? This shouldn't happen in normal flow. Fail closed.
             raise HTTPException(status_code=403, detail="Security trace missing. Cannot proceed.")
        
        if trace_row[0] != "ALLOW":
            # Verdict is DEFUSE, REJECT, or ERROR.
            # We consume the pending row to prevent retries? 
            # Directive says: "delete/keep pending row? (choose deterministic)"
            # Let's DELETE it to prevent a loop of "try again -> blocked".
            cursor.execute("DELETE FROM pending_inbox WHERE id = ?", (payload.input_id,))
            conn.commit()
            return ChatResponse(response="I cannot fulfill this request as it was flagged by safety protocols.")

        # If we are here, Verdict is ALLOW.
        # Clean up (Consumption)
        cursor.execute("DELETE FROM pending_inbox WHERE id = ?", (payload.input_id,))
        conn.commit()
    except HTTPException as he:
        conn.close()
        raise he
    except Exception as e:
        conn.close()
        print(f"[DB ERROR] {e}")
        raise HTTPException(status_code=500, detail="Database error during verification.")
    
    # Connection is still open? No, we need to be careful.
    # We committed and essentially finished the "Transaction".
    # We can close the connection now as we have the data.
    conn.close()

    # 2. Setup Client
    try:
        # MOVED TO ENV: Settings.OPENROUTER_API_KEY
        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
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
        
        # TRACE: COMPLETE
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE request_trace SET sibling_response = ? WHERE id = ?", (reply_text, payload.input_id))
            conn.commit()
            conn.close()
        except Exception: pass

        return ChatResponse(response=reply_text)

    except Exception as e:
        print(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3: IDENTITY (The Source Code) ---
@router.get("/chat/ontology")
async def get_system_ontology():
    """
    Returns the raw philosophical ontology (Source Code of the Soul).
    """
    return {"content": Canon.get_ontology()}
