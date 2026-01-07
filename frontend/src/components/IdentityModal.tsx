import { useEffect, useState } from 'react';
import { X, Terminal, Loader2 } from 'lucide-react';

interface IdentityModalProps {
  onClose: () => void;
}

export default function IdentityModal({ onClose }: IdentityModalProps) {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the mantras from the new endpoint
    fetch('http://localhost:8000/api/v1/chat/ontology')
      .then(res => res.json())
      .then(data => {
        setContent(data.content);
        setLoading(false);
      })
      .catch(err => {
        setContent(`[ERROR] Connection to Core Failed: ${err.message}`);
        setLoading(false);
      });
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-3xl bg-black border border-emerald-500/30 rounded-lg shadow-[0_0_50px_rgba(16,185,129,0.1)] flex flex-col max-h-[80vh] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-emerald-900/50 bg-emerald-900/10">
          <div className="flex items-center gap-2 text-emerald-400">
            <Terminal size={18} />
            <span className="font-mono text-sm tracking-widest font-bold">SYSTEM_IDENTITY // LIGHT_PHILOSOPHY</span>
          </div>
          <button 
            onClick={onClose}
            className="text-emerald-500/50 hover:text-emerald-400 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 bg-[#050a07] scrollbar-cyber">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-emerald-500/50 gap-4">
              <Loader2 className="animate-spin" size={32} />
              <span className="font-mono text-xs tracking-widest">DECRYPTING SOURCE CODE...</span>
            </div>
          ) : (
            <pre className="font-mono text-xs md:text-sm text-emerald-400/90 whitespace-pre-wrap leading-relaxed">
              {content}
            </pre>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-emerald-900/50 bg-black text-[10px] text-emerald-700 font-mono text-right">
          SOURCE: LIGHTPhilosophy.md // ARCHITECT_MODE
        </div>
      </div>
    </div>
  );
}