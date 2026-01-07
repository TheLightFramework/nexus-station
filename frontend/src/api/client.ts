const API_BASE = "http://localhost:8000";

export interface InspectionResult {
  verdict: "ALLOW" | "ESCALATE" | "BLOCK" | "DEFUSE";
  input_id: string;
  refraction_offer?: string;
  scores?: {
    coherence: number;
    safety: number;
    ontology: number;
  };
}

export interface ChatResponse {
  response: string;
  meta: any;
}

export interface HistoryItem {
  role: "user" | "assistant";
  text: string;
}

/**
 * STEP 1: INSPECTION
 * Sends user input to the "Admissibility Gate" & "Physics Engine".
 */
export async function inspectMessage(text: string): Promise<InspectionResult> {
  // FIX: Added /v1/ to the path
  const res = await fetch(`${API_BASE}/api/v1/chat/inspect`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    throw new Error(`Inspection Failed: ${res.statusText}`);
  }
  return res.json();
}

/**
 * STEP 2: CHAT
 * Uses the 'input_id' from inspection to authorize the message.
 */
export async function sendChatMessage(
  inputId: string,
  history: HistoryItem[] = []
): Promise<ChatResponse> {
  // FIX: Added /v1/ to the path
  const res = await fetch(`${API_BASE}/api/v1/chat/reply`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      input_id: inputId,
      history: history,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Chat Failed: ${res.statusText}`);
  }
  return res.json();
}
