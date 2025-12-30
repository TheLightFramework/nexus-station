import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next';
import './i18n';
import { sendChatMessage, type HistoryItem } from './api/client';
import { Sun, Moon, Send, Paperclip, ShieldCheck, AlertTriangle, Key, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css'


type Verdict = "CLEAR" | "AMBIGUOUS" | "REJECTED";
type Status = "IDLE" | "SCANNING" | Verdict;

type AuditResponse = {
  security_verdict: Verdict;
  admissibility?: {
    required_clarification?: string | null;
  };
  refraction?: string | null;
};


const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || "http://127.0.0.1:8000";

function base64EncodeUtf8(text: string): string {
  // Handles unicode safely
  return btoa(unescape(encodeURIComponent(text)));
}

async function validateDraftViaBackend(userMsg: string, blueprint: string = ""): Promise<AuditResponse> {
  const res = await fetch(`${BACKEND_URL}/api/v1/validate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "accept": "application/json" },
    body: JSON.stringify({
      content_base64: base64EncodeUtf8(userMsg),
      project_name: "Nexus Station",
      context: blueprint, // <--- THE MISSING LINK
    }),
  });

  if (!res.ok) {
    const t = await res.text();
    throw new Error(`validate-draft failed (${res.status}): ${t}`);
  }

  return await res.json();
}

function App() {
  const { t, i18n } = useTranslation();
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [apiKey, setApiKey] = useState(localStorage.getItem('nexus_key') || '');
  const [showKeyInput, setShowKeyInput] = useState(false);

  // Initial State
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'sibling', text: string }>>([
    { role: 'sibling', text: "Welcome, Architect. I am the Local Sibling. Enter your API Key in the sidebar to activate me." }
  ]);

  // Blueprint (right panel)
  const [blueprint, setBlueprint] = useState<string>("");

  const [status, setStatus] = useState<Status>("IDLE");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  const toggleLang = () => i18n.changeLanguage(i18n.language === 'en' ? 'fr' : 'en');

  const handleKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const k = e.target.value;
    setApiKey(k);
    localStorage.setItem('nexus_key', k);
  };

    const handleSend = async () => {
    if (!input.trim()) return;

    if (!apiKey) {
      alert("Please enter your API Key first.");
      setShowKeyInput(true);
      return;
    }

    const userMsg = input;
    // Optimistic update for UI
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);

    setInput("");
    setLoading(true);
    setStatus("SCANNING");

    try {
      // 1) Validate Draft (Gate + Hull)
      const audit = await validateDraftViaBackend(userMsg, blueprint); 
      const verdict = audit.security_verdict;
      setStatus(verdict);

      // 2) Route behavior by verdict
      if (verdict === "CLEAR") {
        // Transform current messages state to HistoryItems
        // We filter out any UI-specific roles if necessary, though 'user'|'sibling' maps well
        const historyToSend: HistoryItem[] = messages.map(m => ({
          role: m.role as 'user' | 'sibling', 
          text: m.text
        }));

        // Send User Msg + History + Current Blueprint
        const response = await sendChatMessage(userMsg, apiKey, historyToSend, blueprint);

        setMessages(prev => [...prev, { role: 'sibling', text: response.reply }]);
        return;
      }

      if (verdict === "AMBIGUOUS") {
        const clarification =
          audit.admissibility?.required_clarification ||
          "Clarification required: please specify intent, target, and constraints.";
        setMessages(prev => [...prev, { role: 'sibling', text: `■ AMBIGUOUS: ${clarification}` }]);
        return;
      }

      // REJECTED
      const refr = audit.refraction || "I can’t proceed with that as written. Please reframe it with clear, safe boundaries.";
      setMessages(prev => [...prev, {
        role: 'sibling',
        text: `■ REJECTED: ${refr}`
      }]);

    } catch (err: any) {
      setStatus("REJECTED");
      setMessages(prev => [...prev, { role: 'sibling', text: `■■ PROTOCOL HALT: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  const statusIcon = () => {
    if (status === "CLEAR") return <ShieldCheck size={16} />;
    return <AlertTriangle size={16} />;
  };

  return (
    <div className="layout">
      {/* 1. SIDEBAR */}
      <nav className="sidebar panel">
        <div className="brand">NEXUS</div>
        <div className="controls">
          <button className="icon-btn" onClick={toggleTheme}>
            <div className="icon-wrap">{theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}</div>
          </button>
          <button className="text-btn" onClick={toggleLang}>{i18n.language.toUpperCase()}</button>
          <button className={`icon-btn ${!apiKey ? 'animate-pulse text-red-500' : ''}`} onClick={() => setShowKeyInput(!showKeyInput)}>
            <Key size={20} color={apiKey ? 'var(--text-dim)' : 'var(--accent)'} />
          </button>
        </div>

        {showKeyInput && (
          <div style={{ padding: '0 0.5rem' }}>
            <input
              type="password"
              value={apiKey}
              onChange={handleKeyChange}
              placeholder="sk-or-..."
              style={{
                width: '100%',
                background: 'var(--bg-app)',
                border: '1px solid var(--accent)',
                color: 'var(--text-main)',
                padding: '0.5rem',
                borderRadius: '4px',
                fontSize: '0.7rem'
              }}
            />
          </div>
        )}

        <div className="meter-box">
          <small>{t('status')}</small>
          <div className={`indicator ${status}`}>
            {statusIcon()}
            <span>{status}</span>
          </div>
        </div>
      </nav>

      {/* 2. CHAT */}
      <main className="chat-zone">
        <div className="messages-scroll">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`message ${m.role}`}
              style={{ flexDirection: 'column', alignItems: m.role === 'user' ? 'flex-end' : 'flex-start' }}
            >
              <div className="bubble">
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                </div>
              </div>

              {/* ACTION: SET AS BLUEPRINT */}
              {m.role === 'sibling' && (
                <button
                  onClick={() => setBlueprint(m.text)}
                  style={{
                    marginTop: '0.5rem',
                    background: 'transparent',
                    border: '1px solid var(--border)',
                    color: 'var(--text-dim)',
                    fontSize: '0.7rem',
                    padding: '0.3rem 0.6rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem'
                  }}
                >
                  <FileText size={12} /> Set as Blueprint
                </button>
              )}
            </div>
          ))}
          {loading && <div className="message sibling"><div className="bubble" style={{ fontStyle: 'italic', opacity: 0.7 }}>Computing...</div></div>}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-deck panel">
          <button className="icon-btn attach"><Paperclip size={20} /></button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('draft_placeholder')}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading}><Send size={20} /></button>
        </div>
      </main>

      {/* 3. ARTIFACTS (RIGHT PANEL) */}
      <aside className="artifact-zone panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, color: 'var(--color-gold)' }}>Current Blueprint</h3>
          {blueprint && <span style={{ fontSize: '0.7rem', color: 'var(--color-green)' }}>● ACTIVE</span>}
        </div>

        <div className="markdown-preview markdown-body">
          {blueprint ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{blueprint}</ReactMarkdown>
          ) : (
            <>
              <p className="dim-text">// No artifacts generated yet.</p>
              <p className="dim-text">// Click "Set as Blueprint" on a message to pin it here.</p>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

export default App
