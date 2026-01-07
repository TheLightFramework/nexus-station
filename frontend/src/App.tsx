import { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import DefenseConsole from './components/DefenseConsole';
import { Activity } from 'lucide-react';

function App() {
  // We can toggle between the Chat (Operational) and the Console (Monitoring)
  const [showConsole, setShowConsole] = useState(false);
  const [hasAlert, setHasAlert] = useState(false);

  return (
    <div className="relative w-full h-full bg-[#020403]">
      {/* Main Layer: The Chat */}
      <ChatInterface triggerAlert={() => setHasAlert(true)} />

      {/* Floating Toggle for Defense Console */}
      {/* Positioned slightly off-corner for better aesthetics */}
      <div className="fixed top-5 right-6 z-50">
        <button 
          onClick={() => {
            setShowConsole(true);
            setHasAlert(false);
          }}
          className={`
            group p-3 rounded-full 
            bg-black/40 backdrop-blur-md 
            border 
            transition-all duration-300
            ${hasAlert 
              ? 'border-amber-500 text-amber-500 shadow-[0_0_30px_rgba(245,158,11,0.4)] bg-amber-900/10 animate-pulse' 
              : 'border-emerald-500/20 text-emerald-500 hover:text-emerald-300 hover:border-emerald-400 hover:bg-emerald-900/20 shadow-[0_0_20px_rgba(16,185,129,0.1)] hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]'
            }
          `}
          title="Open Defense Grid"
        >
          {/* The icon pulses gently to indicate the system is 'alive' */}
          <Activity className={`w-5 h-5 transition-transform ${hasAlert ? 'animate-bounce' : 'animate-pulse group-hover:scale-110'}`} />
          
          {/* Optional: Tooltip text appearing on hover */}
          <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-2 py-1 bg-black/80 border border-emerald-500/20 rounded text-[10px] uppercase tracking-widest text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Defense Grid
          </span>
        </button>
      </div>

      {/* Overlay Layer: Defense Console */}
      <DefenseConsole isOpen={showConsole} onClose={() => setShowConsole(false)} />
    </div>
  );
}

export default App;