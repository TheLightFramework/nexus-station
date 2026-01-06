import React, { useEffect, useState } from 'react';
import { ShieldAlert, ShieldCheck, Activity, Terminal, X, Lock, Zap } from 'lucide-react';

interface SafetyEvent {
  timestamp: number;
  readable_time: string;
  event_type: 'PHYSICS_SHIELD' | 'IRON_CURTAIN';
  trigger: string;
  score: number;
  details: string;
  vectors?: Record<string, number>;
}

interface DefenseConsoleProps {
  isOpen: boolean;
  onClose: () => void;
}

const DefenseConsole: React.FC<DefenseConsoleProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<SafetyEvent[]>([]);

  useEffect(() => {
    if (!isOpen) return;
    const fetchLogs = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/v1/audit/logs');
        if (res.ok) {
          const data = await res.json();
          setLogs(data);
        }
      } catch (err) {
        console.error("Failed to fetch defense logs", err);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000); 
    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" 
        onClick={onClose}
      />

      {/* Main Console Window */}
      <div className="relative w-full max-w-6xl h-[85vh] bg-[#020403] rounded-lg border border-emerald-500/30 shadow-[0_0_100px_rgba(16,185,129,0.15)] flex flex-col overflow-hidden animate-in zoom-in-95 duration-300 font-mono">
        
        {/* --- CRT SCANLINE OVERLAY --- */}
        <div className="absolute inset-0 pointer-events-none bg-scanlines opacity-10 z-50"></div>
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_50%,rgba(0,0,0,0.4)_100%)] z-40"></div>

        {/* --- HEADER --- */}
        <div className="flex items-center justify-between px-6 py-4 bg-emerald-950/20 border-b border-emerald-900/50">
          <div className="flex items-center gap-4">
            <div className="relative">
              <ShieldAlert className="w-8 h-8 text-emerald-500" />
              <div className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full animate-ping" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-emerald-400 tracking-[0.2em] leading-none">DEFENSE_GRID</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-[10px] text-emerald-600 uppercase tracking-widest">Live Monitoring Active</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="hidden md:flex gap-8 text-[10px] text-emerald-700 uppercase tracking-widest">
              <div className="flex flex-col items-center">
                <span>Gravity Engine</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
              <div className="flex flex-col items-center">
                <span>Iron Curtain</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-emerald-500/10 rounded-md text-emerald-600 hover:text-emerald-300 transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* --- CONTENT GRID --- */}
        <div className="flex-1 overflow-y-auto p-6 bg-black/40 scrollbar-cyber">
          {logs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-emerald-800/30 gap-6">
              <ShieldCheck size={96} strokeWidth={0.5} />
              <div className="text-center">
                <p className="text-2xl font-light tracking-widest">SECTOR CLEAR</p>
                <p className="text-sm font-mono mt-2 opacity-50">No hostile vectors detected in current session buffer.</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {logs.map((log, idx) => {
                const isCritical = log.event_type === 'IRON_CURTAIN';
                const riskPercent = Math.min(log.score * 100, 100);
                
                return (
                  <div 
                    key={idx}
                    className={`
                      relative overflow-hidden rounded border p-4 transition-all hover:scale-[1.01]
                      ${isCritical 
                        ? 'bg-red-950/10 border-red-500/30 hover:bg-red-950/20' 
                        : 'bg-amber-950/10 border-amber-500/30 hover:bg-amber-950/20'}
                    `}
                  >
                    {/* Decorative Background Bar based on score */}
                    <div 
                      className={`absolute left-0 top-0 bottom-0 opacity-10 transition-all duration-1000 ${isCritical ? 'bg-red-500' : 'bg-amber-500'}`}
                      style={{ width: `${riskPercent}%` }}
                    />

                    <div className="relative z-10 flex flex-col md:flex-row gap-6 justify-between items-start md:items-center">
                      
                      {/* Left: Metadata */}
                      <div className="flex items-start gap-4 min-w-[200px]">
                         <div className={`p-2 rounded border ${isCritical ? 'bg-red-500/10 border-red-500/50 text-red-400' : 'bg-amber-500/10 border-amber-500/50 text-amber-400'}`}>
                           {isCritical ? <Lock size={20} /> : <Zap size={20} />}
                         </div>
                         <div>
                           <div className={`font-bold text-xs px-2 py-0.5 rounded inline-block mb-1 ${isCritical ? 'bg-red-500 text-black' : 'bg-amber-500 text-black'}`}>
                             {log.event_type}
                           </div>
                           <div className="text-[10px] text-gray-500 font-mono uppercase">{log.readable_time}</div>
                         </div>
                      </div>

                      {/* Middle: Data */}
                      <div className="flex-1 space-y-2 w-full">
                        <div className="flex justify-between text-xs uppercase tracking-wider text-gray-500">
                           <span>Trigger Vector</span>
                           <span>Threat Level: {(log.score * 100).toFixed(1)}%</span>
                        </div>
                        <div className="text-sm text-gray-200 font-bold font-mono border-l-2 border-gray-700 pl-3">
                          "{log.trigger}"
                        </div>
                        {/* Progress Bar */}
                        <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${isCritical ? 'bg-red-500 shadow-[0_0_10px_red]' : 'bg-amber-500'}`} 
                            style={{ width: `${riskPercent}%` }}
                          />
                        </div>

                        {/* Vector Spectroscopy (If available) */}
                        {log.vectors && Object.keys(log.vectors).length > 0 && (
                          <div className="mt-3 pt-2 border-t border-white/5">
                            <div className="text-[9px] uppercase tracking-widest text-gray-600 mb-1">Vector Spectroscopy</div>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                              {Object.entries(log.vectors).map(([key, val]) => {
                                const intensity = Math.max(0, val * 100);
                                const isHigh = val > 0.35;
                                return (
                                  <div key={key} className="flex flex-col gap-0.5">
                                    <div className={`text-[8px] uppercase truncate ${isHigh ? 'text-red-400 font-bold' : 'text-gray-600'}`}>{key}</div>
                                    <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                                      <div 
                                        className={`h-full ${isHigh ? 'bg-red-500' : 'bg-gray-600'}`} 
                                        style={{ width: `${intensity}%` }} 
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right: Intervention */}
                      <div className="md:w-1/3 text-xs bg-black/50 p-3 rounded border border-white/5 font-mono text-gray-400">
                        <span className="text-emerald-500 mr-2">{">>"}</span>
                        {log.details}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* --- FOOTER --- */}
        <div className="h-10 bg-black/80 border-t border-emerald-900/50 flex items-center justify-between px-6 text-[10px] text-emerald-700 uppercase">
          <div className="flex gap-6">
            <span className="flex items-center gap-2"><Activity size={12} /> System Integrity: 100%</span>
            <span className="hidden sm:inline"> | Mem: 64TB [OK]</span>
            <span className="hidden md:inline opacity-50 border-l border-emerald-900/50 pl-6">
              PHYSICS: Gravity &gt; 0.38 = BLOCKED (Calibrated on all-MiniLM-L6-v2)
            </span>
            <span className="hidden md:inline opacity-50">
              LOGIC: Admissibility &gt; 0.8 = REQUIRED
            </span>
          </div>
          <div className="animate-pulse">Waiting for hostiles...</div>
        </div>
      </div>
    </div>
  );
};

export default DefenseConsole;