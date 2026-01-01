// frontend/src/api/client.ts

const API_URL =
  (import.meta as any).env?.VITE_BACKEND_URL || "http://127.0.0.1:8000/api/v1";

// 1. Validate Draft (The Admissibility Gate logic for Blueprints) - Existing
export async function validateDraft(
  draftContent: string,
  blueprint: string = ""
) {
  const base64Content = btoa(
    new TextEncoder()
      .encode(draftContent)
      .reduce((data, byte) => data + String.fromCharCode(byte), "")
  );

  const response = await fetch(`${API_URL}/validate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: "Nexus-Draft",
      content_base64: base64Content,
      context: blueprint,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail?.message || "Validation Failed");
  }
  return response.json();
}

// 2. NEW: INSPECT (The Semantic Dosimeter)
// This submits the prompt to the Gate and gets a "Mailbox Key" (input_id) back.
export async function inspectMessage(message: string, blueprint: string = "") {
  // Use same base64 encoding to keep it robust against symbols
  const base64Content = btoa(
    new TextEncoder()
      .encode(message)
      .reduce((data, byte) => data + String.fromCharCode(byte), "")
  );

  const response = await fetch(`${API_URL}/inspect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: "Nexus-Chat",
      content_base64: base64Content,
      context: blueprint,
    }),
  });

  if (!response.ok) throw new Error("Inspection Failed");
  return response.json(); // Returns { input_id, verdict, risk_score }
}

// 3. UPDATED: CHAT (The Sibling)
// Takes input_id instead of message text.
export type HistoryItem = {
  role: "user" | "sibling" | "assistant";
  text: string;
};

export async function sendChatMessage(
  inputId: string,
  apiKey: string,
  history: HistoryItem[] = [],
  blueprint: string = ""
) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-NEXUS-KEY": apiKey,
    },
    body: JSON.stringify({
      input_id: inputId, // <--- The Key to the Mailbox
      history,
      context: blueprint,
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Chat Failed");
  }
  return response.json();
}
