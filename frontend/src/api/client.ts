// Simple fetch wrapper to talk to FastAPI
const API_URL =
  (import.meta as any).env?.VITE_BACKEND_URL || "http://127.0.0.1:8000/api/v1";

export async function validateDraft(draftContent: string) {
  // 1. Base64 Encode (The Security Requirement)
  // btoa works for ASCII, for Unicode we need a small hack or a library.
  // Using a robust one-liner for utf-8 support:
  const base64Content = btoa(
    new TextEncoder()
      .encode(draftContent)
      .reduce((data, byte) => data + String.fromCharCode(byte), "")
  );

  const response = await fetch(`${API_URL}/validate-draft`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      project_name: "Genesis-Draft-001",
      content_base64: base64Content,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail?.message || "Audit Failed");
  }

  return response.json();
}

export type HistoryItem = {
  role: "user" | "sibling" | "assistant";
  text: string;
};

export async function sendChatMessage(
  message: string,
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
      message,
      history,
      context: blueprint, // Mapping 'blueprint' to the 'context' field in backend schema
    }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Chat Failed");
  }
  return response.json();
}
