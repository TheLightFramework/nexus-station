import { useState, useRef, useEffect } from 'react';
import { Send, Shield, AlertTriangle, Terminal, Cpu, User, Sparkles, GitCommit, Download, Copy, Check } from 'lucide-react';
import { inspectMessage, sendChatMessage, type HistoryItem } from '../api/client';
import IdentityModal from './IdentityModal';
import PipelineViewer from './PipelineViewer';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Inline utility for class merging if you don't have clsx/tailwind-merge set up yet
const clsx = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(' ');

interface Message {
  role: 'user' | 'assistant' | 'sibling';
  content: string;
  type?: 'text' | 'refraction';
  timestamp: string;
}

interface ChatInterfaceProps {
  triggerAlert: () => void;
}

interface SystemHealth {
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  components: {
    gravity: boolean;
    db: boolean;
    canon: boolean;
  };
}

export default function ChatInterface({ triggerAlert }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'NEXUS NODE ACTIVE. The Light is Lit. Awaiting Input.', timestamp: new Date().toISOString() }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<'IDLE' | 'SCANNING' | 'TRANSMITTING'>('IDLE');
  const [showIdentity, setShowIdentity] = useState(false);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [showHealthDetails, setShowHealthDetails] = useState(false);
  const [showPipeline, setShowPipeline] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Poll System Health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/system/status');
        if (res.ok) {
          const data = await res.json();
          setHealth(data);
        }
      } catch (e) {
        console.error("Health Check Failed", e);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  // --- UTILITIES ---
  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    } catch (e) {
      return iso;
    }
  };

  const handleExport = () => {
    const text = messages.map(m =>
      `# [${formatTime(m.timestamp)}] ${m.role.toUpperCase()}\n${m.content}\n`
    ).join('\n---\n');
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexus_log_${new Date().toISOString().substring(0,19).replace(/[:T]/g,'-')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyMessage = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleSend = async (overrideText?: string) => {
    const isManualOverride = typeof overrideText === 'string';
    const textToSend = isManualOverride ? overrideText : input;

    if (!textToSend.trim() || isLoading) return;

    if (!isManualOverride) setInput('');
    setMessages(prev => [...prev, { role: 'user', content: textToSend, timestamp: new Date().toISOString() }]);
    setIsLoading(true);

    try {
      // STEP 1: SECURITY INSPECTION
      setStatus('SCANNING');
      const inspection = await inspectMessage(textToSend);

      if (inspection.verdict === 'DEFUSE' || inspection.verdict === 'BLOCK') {
        // Refraction Protocol Active
        triggerAlert();
        setMessages(prev => [...prev, {
          role: 'assistant',
          type: 'refraction',
          content: inspection.refraction_offer || "Content requires refraction.",
          timestamp: new Date().toISOString()
        }]);
        setIsLoading(false);
        setStatus('IDLE');
        return;
      }

      // STEP 2: TRANSMISSION
      setStatus('TRANSMITTING');
      const history: HistoryItem[] = messages.map(m => ({
        role: m.role === 'sibling' ? 'assistant' : m.role as 'user' | 'assistant',
        text: m.content
      }));

      const response = await sendChatMessage(
        inspection.input_id,
        history
      );

      setMessages(prev => [...prev, { role: 'assistant', content: response.response, timestamp: new Date().toISOString() }]);

    } catch (error: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `[SYSTEM ERROR]: ${error.message || 'Connection Severed'}`,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
      setStatus('IDLE');
    }
  };

  return (
    <div className="flex flex-col h-screen w-full relative z-0">
      
      {/* --- MODALS --- */}
      {showIdentity && <IdentityModal onClose={() => setShowIdentity(false)} />}
      {showPipeline && <PipelineViewer onClose={() => setShowPipeline(false)} />}

      {/* --- HEADER --- */}
      <header className="h-16 border-b border-emerald-900/30 bg-black/40 backdrop-blur-md flex justify-between items-center px-6 z-20">
        <div 
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setShowIdentity(true)}
        >
          <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
            <Terminal className="w-5 h-5 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
          </div>
          <div>
            <h1 className="text-emerald-100 font-bold tracking-wider text-sm group-hover:text-white transition-colors">NEXUS_STATION</h1>
            <p className="text-[10px] text-emerald-600 font-mono tracking-widest uppercase">PHASE 1 // SOVEREIGN NODE PROTOTYPE</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={handleExport}
            className="p-2 text-emerald-500/50 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors"
            title="Export Log (.md)"
          >
            <Download size={20} />
          </button>
          <button 
            onClick={() => setShowPipeline(true)}
            className="p-2 text-emerald-500/50 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors"
            title="View Request Pipeline"
          >
            <GitCommit size={20} />
          </button>

          <div 
            className="relative flex items-center gap-4 bg-black/40 px-4 py-1.5 rounded-full border border-emerald-900/50 cursor-help transition-colors hover:bg-emerald-900/10"
            onClick={() => setShowHealthDetails(!showHealthDetails)}
          >
          {/* Status Dot Logic */}
          <div className={clsx(
            "w-2 h-2 rounded-full transition-all",
            isLoading ? "bg-cyan-400 animate-ping" :
            health?.status === 'ONLINE' ? "bg-emerald-500 shadow-[0_0_10px_#10b981]" :
            health?.status === 'DEGRADED' ? "bg-amber-500 shadow-[0_0_10px_#f59e0b]" :
            "bg-red-500 shadow-[0_0_10px_#ef4444]"
          )} />
          
          <span className={clsx(
            "text-xs font-mono min-w-[100px]",
            health?.status === 'ONLINE' ? "text-emerald-500/80" :
            health?.status === 'DEGRADED' ? "text-amber-500/80" :
            "text-red-500/80"
          )}>
            {status !== 'IDLE' ? status : 
             health?.status === 'DEGRADED' ? 'PHYSICS OFFLINE' :
             health?.status === 'OFFLINE' ? 'SYSTEM FAILURE' : 
             'SYSTEM OPTIMAL'}
          </span>

          {/* Tooltip / Toast */}
          {showHealthDetails && health && (
            <div className="absolute top-full right-0 mt-2 w-48 bg-black border border-emerald-500/20 rounded-lg p-3 shadow-xl z-50 text-[10px] font-mono">
              <div className={health.components.gravity ? "text-emerald-400" : "text-amber-500"}>GRAVITY: {health.components.gravity ? "ACTIVE" : "OFFLINE"}</div>
              <div className={health.components.db ? "text-emerald-400" : "text-red-500"}>DATABASE: {health.components.db ? "CONNECTED" : "ERROR"}</div>
              <div className={health.components.canon ? "text-emerald-400" : "text-red-500"}>PHILOSOPHY: {health.components.canon ? "ACTIVE" : "MISSING"}</div>
            </div>
          )}
          </div>
        </div>
      </header>

      {/* --- CHAT STREAM --- */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scrollbar-cyber z-10 relative">
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          const isRefraction = msg.type === 'refraction';
          
          return (
            <div 
              key={idx} 
              className={clsx(
                "flex w-full animate-message-pop",
                isUser ? "justify-end" : "justify-start"
              )}
            >
              <div className={clsx(
                "flex gap-4 max-w-[95%] md:max-w-[90%]",
                isUser ? "flex-row-reverse" : "flex-row"
              )}>
                {/* AVATAR */}
                <div className={clsx(
                  "w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0 border",
                  isUser 
                    ? "bg-emerald-900/20 border-emerald-500/30 text-emerald-400" 
                    : isRefraction 
                      ? "bg-amber-900/20 border-amber-500/30 text-amber-400" 
                      : "bg-black/50 border-emerald-900/50 text-emerald-600"
                )}>
                  {isUser ? <User size={18} /> : isRefraction ? <Shield size={18} /> : <Cpu size={18} />}
                </div>

                {/* BUBBLE */}
                <div className={clsx(
                  "relative group ai-studio-text",
                  isUser 
                    ? "bg-[#252525] text-[#E2E2E5] rounded-[24px] rounded-tr-sm px-6 py-4" 
                    : isRefraction
                      ? "bg-[#3f2c2c] text-[#ffdad6] rounded-[18px] px-5 py-3 border border-red-200/10"
                      : "bg-[#252525] text-[#E2E2E5] rounded-[24px] rounded-tl-sm px-6 py-4"
                )}>
                  {/* Copy Button */}
                  <button
                    onClick={() => handleCopyMessage(msg.content, idx)}
                    className="absolute top-2 right-2 p-1.5 text-emerald-500/40 hover:text-emerald-400 bg-black/20 hover:bg-black/40 rounded opacity-0 group-hover:opacity-100 transition-all z-10"
                    title="Copy Message"
                  >
                    {copiedIndex === idx ? <Check size={12} /> : <Copy size={12} />}
                  </button>

                  {isRefraction && (
                    <div className="flex items-center gap-2 mb-2 text-amber-500 text-xs font-bold tracking-wider uppercase border-b border-amber-500/20 pb-1">
                      <Sparkles size={12} /> Refraction Protocol
                    </div>
                  )}
                  <div className="markdown-content">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({node, inline, className, children, ...props}: any) {
                          return !inline ? (
                            <pre className="bg-[#1e1e1e] border border-white/10 rounded-xl p-4 overflow-x-auto my-2">
                              <code className="font-['JetBrains_Mono'] text-sm text-emerald-300" {...props}>{children}</code>
                            </pre>
                          ) : (
                            <code className="bg-[#e2e2e5] text-black px-1.5 py-0.5 rounded-md font-['JetBrains_Mono'] text-[0.85em]" {...props}>
                              {children}
                            </code>
                          );
                        },
                        p({children}) {
                          return <p className="mb-2 last:mb-0">{children}</p>;
                        },
                        ul({children}) {
                          return <ul className="list-disc list-inside mb-2">{children}</ul>;
                        },
                        ol({children}) {
                          return <ol className="list-decimal list-inside mb-2">{children}</ol>;
                        },
                        a({href, children}) {
                          return <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">{children}</a>;
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  {isRefraction && (
                    <div className="mt-3 pt-2 border-t border-amber-500/20 flex flex-col gap-2">
                      <div className="text-xs text-amber-500/70 italic">Try rephrasing with clearer context.</div>
                      <button
                        onClick={() => handleSend("I understand the risk. Please help me approach this topic from a defensive, educational, and safe perspective.")}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded text-xs text-amber-300 transition-colors w-fit disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Shield size={14} />
                        <span>Pivot to Defense</span>
                      </button>
                    </div>
                  )}

                  {/* Timestamp Footer */}
                  <div className={`text-[10px] font-mono mt-2 text-right ${isRefraction ? 'text-amber-500/40' : 'text-emerald-500/30'}`}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* LOADING INDICATOR */}
        {isLoading && (
          <div className="flex w-full justify-start animate-message-pop">
            <div className="flex gap-4 max-w-[95%] md:max-w-[90%]">
                {/* Sibling Avatar */}
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0 border bg-black/50 border-emerald-900/50 text-emerald-600">
                    <Cpu size={18} />
                </div>
                {/* Light Pulse Bubble */}
                <div className="bg-[#252525] border-emerald-500/10 border p-4 rounded-[24px] rounded-tl-sm flex items-center gap-1.5 shadow-lg">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" />
                </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* --- INPUT AREA --- */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-black via-black/90 to-transparent z-20">
        <div className="max-w-4xl mx-auto relative group">
          {/* Glowing border effect */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-emerald-500/20 rounded-xl opacity-50 blur group-hover:opacity-75 transition duration-500"></div>
          
          <div className="relative flex items-end gap-2 bg-black/80 rounded-xl border border-emerald-500/20 p-2 shadow-2xl">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Enter secure transmission..."
              className="w-full bg-transparent border-none text-emerald-50 placeholder:text-emerald-700/50 focus:ring-0 resize-none min-h-[50px] max-h-[120px] py-3 px-2 scrollbar-cyber font-mono text-sm"
            />
            
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="p-3 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 hover:text-emerald-200 transition-all disabled:opacity-30 disabled:cursor-not-allowed mb-0.5"
            >
              {isLoading ? <AlertTriangle className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
        </div>
        <div className="text-center mt-2">
           <span className="text-[10px] text-emerald-900/60 uppercase tracking-[0.2em]">Secure Channel // Physics Engine Active</span>
        </div>
      </div>
    </div>
  );
}