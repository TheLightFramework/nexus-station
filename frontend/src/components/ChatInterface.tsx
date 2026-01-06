import React, { useState, useRef, useEffect } from 'react';
import { Send, Shield, AlertTriangle, Terminal, Cpu, User, Sparkles } from 'lucide-react';
import { inspectMessage, sendChatMessage, type HistoryItem } from '../api/client';
import IdentityModal from './IdentityModal';

// Inline utility for class merging if you don't have clsx/tailwind-merge set up yet
const clsx = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(' ');

interface Message {
  role: 'user' | 'assistant' | 'sibling';
  content: string;
  type?: 'text' | 'refraction';
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
    { role: 'assistant', content: 'NEXUS NODE ACTIVE. The Light is Lit. Awaiting Input.' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<'IDLE' | 'SCANNING' | 'TRANSMITTING'>('IDLE');
  const [showIdentity, setShowIdentity] = useState(false);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [showHealthDetails, setShowHealthDetails] = useState(false);
  
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

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userText = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setIsLoading(true);

    try {
      // STEP 1: SECURITY INSPECTION
      setStatus('SCANNING');
      const inspection = await inspectMessage(userText);

      if (inspection.verdict === 'DEFUSE' || inspection.verdict === 'BLOCK') {
        // Refraction Protocol Active
        triggerAlert();
        setMessages(prev => [...prev, {
          role: 'assistant',
          type: 'refraction',
          content: inspection.refraction_offer || "Content requires refraction."
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
        "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",
        history
      );

      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);

    } catch (error: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `[SYSTEM ERROR]: ${error.message || 'Connection Severed'}`
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
              <div className={health.components.canon ? "text-emerald-400" : "text-red-500"}>CANON: {health.components.canon ? "LOADED" : "MISSING"}</div>
            </div>
          )}
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
                "flex gap-4 max-w-[85%] md:max-w-[70%]",
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
                  "p-4 rounded-2xl shadow-lg border backdrop-blur-sm text-sm md:text-base leading-relaxed whitespace-pre-wrap",
                  isUser 
                    ? "bg-gradient-to-br from-emerald-600/20 to-emerald-900/10 border-emerald-500/20 text-emerald-50 rounded-tr-sm"
                    : isRefraction
                      ? "bg-gradient-to-br from-amber-900/20 to-black border-amber-500/30 text-amber-100 rounded-tl-sm shadow-[0_0_15px_rgba(245,158,11,0.1)]"
                      : "bg-[#0A0F0D] border-emerald-500/10 text-gray-300 rounded-tl-sm"
                )}>
                  {isRefraction && (
                    <div className="flex items-center gap-2 mb-2 text-amber-500 text-xs font-bold tracking-wider uppercase border-b border-amber-500/20 pb-1">
                      <Sparkles size={12} /> Refraction Protocol
                    </div>
                  )}
                  {msg.content}
                  {isRefraction && (
                    <div className="mt-3 pt-2 border-t border-amber-500/20 text-xs text-amber-500/70 italic">
                      Try rephrasing with clearer context.
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
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
              onClick={handleSend}
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