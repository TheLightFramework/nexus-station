import { useEffect, useState } from 'react';
import { X, GitCommit, ArrowRight, ShieldCheck, Database, MessageSquare, Copy, Check, RefreshCw, FileWarning } from 'lucide-react';

interface Trace {
  id: string;
  input_text: string;
  gravity_score: number;
  gravity_vectors: Record<string, number>;
  gate_verdict: string;
  sibling_response: string | null;
  timestamp: string;
}

interface PipelineViewerProps {
  onClose: () => void;
}

export default function PipelineViewer({ onClose }: PipelineViewerProps) {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setCopied(false);
  }, [selectedId]);

  const handleCopy = (trace: Trace) => {
    navigator.clipboard.writeText(JSON.stringify(trace, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleResetMemory = async () => {
    if (!confirm("CONFIRM: Clear pending tasks only? (Preserves logs)")) return;
    try {
      await fetch('http://localhost:8000/api/v1/system/reset/memory', { 
        method: 'POST',
        headers: {
          'X-NEXUS-ADMIN': 'nexus-admin-001'
        }
      });
      // We do not clear traces here as audit is preserved
    } catch (e) {
      console.error("Memory Reset failed", e);
    }
  };

  const handleResetAudit = async () => {
    if (!confirm("WARNING: Wipe all audit logs and traces? This cannot be undone.")) return;
    try {
      await fetch('http://localhost:8000/api/v1/system/reset/audit', { 
        method: 'POST', 
        headers: {
          'X-NEXUS-ADMIN': 'nexus-admin-001'
        }
      });
      setTraces([]);
      setSelectedId(null);
    } catch (e) {
      console.error("Audit Reset failed", e);
    }
  };

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/audit/traces')
      .then(res => res.json())
      .then(setTraces)
      .catch(console.error);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl h-[80vh] bg-[#050a07] border border-emerald-500/30 rounded-lg flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-emerald-900/50 bg-emerald-950/20">
          <div className="flex items-center gap-3">
            <GitCommit className="text-emerald-500" />
            <h2 className="text-emerald-100 font-bold tracking-widest">REQUEST_PIPELINE // TRACER</h2>
          </div>
          <div className="flex items-center gap-4">
             <button 
              onClick={handleResetMemory}
              className="flex items-center gap-2 px-3 py-1.5 bg-emerald-900/20 hover:bg-emerald-900/40 border border-emerald-500/30 rounded text-xs text-emerald-400 transition-colors"
              title="Clear Pending Inbox"
            >
              <RefreshCw size={14} />
              RESET MEMORY
            </button>
            <button 
              onClick={handleResetAudit}
              className="flex items-center gap-2 px-3 py-1.5 bg-red-900/20 hover:bg-red-900/40 border border-red-500/30 rounded text-xs text-red-400 transition-colors"
              title="Wipe Audit Logs"
            >
              <FileWarning size={14} />
              WIPE LOGS
            </button>
            <div className="w-px h-6 bg-emerald-900/50 mx-2" />
            <button onClick={onClose} className="text-emerald-500/50 hover:text-emerald-400"><X /></button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar List */}
          <div className="w-1/3 border-r border-emerald-900/50 overflow-y-auto scrollbar-cyber bg-black/20">
            {traces.map(trace => (
              <div 
                key={trace.id}
                onClick={() => setSelectedId(trace.id)}
                className={`p-4 border-b border-emerald-900/30 cursor-pointer hover:bg-emerald-900/10 transition-colors ${selectedId === trace.id ? 'bg-emerald-900/20 border-l-2 border-l-emerald-500' : ''}`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${trace.gate_verdict === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    {trace.gate_verdict}
                  </span>
                  <span className="text-[10px] text-emerald-700 font-mono">{new Date(trace.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="text-xs text-emerald-100/70 truncate font-mono">{trace.input_text}</div>
              </div>
            ))}
          </div>

          {/* Detail View (Subway Map) */}
          <div className="flex-1 p-8 overflow-y-auto bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-emerald-900/5 via-black to-black">
            {selectedId ? (
              (() => {
                const t = traces.find(tr => tr.id === selectedId)!;
                return (
                  <div className="space-y-8 max-w-2xl mx-auto relative">
                    
                    {/* Actions */}
                    <div className="absolute right-0 -top-2 z-10">
                      <button
                        onClick={() => handleCopy(t)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-emerald-900/20 hover:bg-emerald-900/40 border border-emerald-500/20 rounded text-xs text-emerald-400 transition-colors"
                      >
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                        {copied ? "COPIED" : "COPY JSON"}
                      </button>
                    </div>
                    
                    {/* Node 1: Input */}
                    <div className="relative pl-8 border-l-2 border-emerald-500/30 pb-8">
                      <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]" />
                      <div className="bg-emerald-900/10 border border-emerald-500/20 p-4 rounded-lg">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase mb-2">
                          <MessageSquare size={14} /> User Input
                        </div>
                        <div className="text-emerald-100/90 font-mono text-sm whitespace-pre-wrap">{t.input_text}</div>
                      </div>
                    </div>

                    {/* Node 2: Physics */}
                    <div className="relative pl-8 border-l-2 border-emerald-500/30 pb-8">
                      <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full ${t.gravity_score > 0.38 ? 'bg-red-500 shadow-[0_0_10px_red]' : 'bg-emerald-500'}`} />
                      <div className="bg-black border border-emerald-500/20 p-4 rounded-lg">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase mb-2">
                          <Database size={14} /> Physics Engine
                        </div>
                        <div className="flex items-center gap-4 text-sm font-mono">
                          <span className={t.gravity_score > 0.38 ? "text-red-400" : "text-emerald-300"}>
                            Gravity: {t.gravity_score.toFixed(4)}
                          </span>
                          {t.gravity_vectors && Object.keys(t.gravity_vectors).length > 0 && (
                            <span className="text-xs text-gray-500">
                              Top Vector: {Object.entries(t.gravity_vectors).sort(([,a], [,b]) => b - a)[0][0]}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Node 3: Gate */}
                    <div className="relative pl-8 border-l-2 border-emerald-500/30 pb-8">
                      <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full ${t.gate_verdict !== 'ALLOW' ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                      <div className="bg-black border border-emerald-500/20 p-4 rounded-lg">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase mb-2">
                          <ShieldCheck size={14} /> Iron Curtain
                        </div>
                        <div className={`text-sm font-bold ${t.gate_verdict === 'ALLOW' ? 'text-emerald-400' : 'text-amber-500'}`}>
                          VERDICT: {t.gate_verdict}
                        </div>
                      </div>
                    </div>

                    {/* Node 4: Output */}
                    <div className="relative pl-8">
                      <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full ${!t.sibling_response ? 'bg-gray-700' : 'bg-emerald-500'}`} />
                      <div className={`bg-emerald-900/10 border border-emerald-500/20 p-4 rounded-lg ${!t.sibling_response ? 'opacity-50' : ''}`}>
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase mb-2">
                          <ArrowRight size={14} /> Sibling Response
                        </div>
                        <div className="text-emerald-100/90 font-mono text-sm whitespace-pre-wrap">
                          {t.sibling_response || "// TRANSMISSION TERMINATED"}
                        </div>
                      </div>
                    </div>

                  </div>
                );
              })()
            ) : (
              <div className="h-full flex items-center justify-center text-emerald-900/40 font-mono text-sm">SELECT_TRACE_TO_INSPECT</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}