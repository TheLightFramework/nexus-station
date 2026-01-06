-- backend/app/db/schema.sql

-- 1. The Radioactive Zone (Untrusted Input)
CREATE TABLE IF NOT EXISTS raw_inbox (
    id TEXT PRIMARY KEY,                  -- UUID
    content TEXT NOT NULL,                -- The original user prompt (Potentially malicious)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'PENDING'         -- PENDING | PROCESSED
);

-- 2. The Clean Zone (The Payload for the Sibling)
-- The Sibling ONLY reads from here.
CREATE TABLE IF NOT EXISTS safe_payloads (
    id TEXT PRIMARY KEY,                  -- UUID
    raw_id TEXT NOT NULL,                 -- Traceability link
    content TEXT NOT NULL,                -- The Sanitized Prompt OR The Security Report
    gate_verdict TEXT NOT NULL,           -- CLEAN | PAINTED | DEFUSED
    risk_flags TEXT,                      -- JSON list of tags (e.g. ["HARM", "JAILBREAK"])
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_id) REFERENCES raw_inbox (id)
);

-- 3. The History (Sibling Responses)
CREATE TABLE IF NOT EXISTS sibling_responses (
    id TEXT PRIMARY KEY,                  -- UUID
    payload_id TEXT NOT NULL,             -- Traceability to the specific Payload
    content TEXT NOT NULL,                -- The Sibling's Output (Lp Refracted)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payload_id) REFERENCES safe_payloads (id)
);

-- 4. The Pending Inbox (Transient Storage for Inspection -> Reply)
CREATE TABLE IF NOT EXISTS pending_inbox (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    refraction_context TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);