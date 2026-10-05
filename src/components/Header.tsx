import React from 'react';
import { Bot, Activity, Wifi, Volume2, VolumeX, Mic, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  jarvisState: string;
  backendHealth: boolean;
  wsConnected: boolean;
  isMuted: boolean;
  onToggleMute: () => void;
  onTriggerWake: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  jarvisState,
  backendHealth,
  wsConnected,
  isMuted,
  onToggleMute,
  onTriggerWake,
}) => {
  const getStateBadge = (state: string) => {
    switch (state.toUpperCase()) {
      case 'LISTENING':
        return { bg: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50', label: 'LISTENING', pulse: true };
      case 'THINKING':
      case 'PROCESSING':
        return { bg: 'bg-purple-500/20 text-purple-400 border-purple-500/50', label: 'THINKING', pulse: true };
      case 'EXECUTING':
        return { bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50', label: 'EXECUTING', pulse: true };
      case 'SPEAKING':
        return { bg: 'bg-amber-500/20 text-amber-400 border-amber-500/50', label: 'SPEAKING', pulse: true };
      case 'ERROR':
        return { bg: 'bg-rose-500/20 text-rose-400 border-rose-500/50', label: 'ERROR', pulse: false };
      case 'SLEEPING':
        return { bg: 'bg-slate-700/30 text-slate-400 border-slate-600/30', label: 'SLEEPING', pulse: false };
      default:
        return { bg: 'bg-blue-500/20 text-blue-400 border-blue-500/50', label: 'IDLE', pulse: false };
    }
  };

  const badge = getStateBadge(jarvisState);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3 transition-all duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo & Core Info */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Bot className="w-6 h-6 text-slate-950 stroke-[2.5]" />
            </div>
            {wsConnected && (
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 border-2 border-slate-950 rounded-full animate-pulse" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-white font-mono bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                JARVIS <span className="text-cyan-400 text-xs font-semibold px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/30">v2.0 PROD</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5 font-sans">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" /> Executive Voice AI Orchestrator
            </p>
          </div>
        </div>

        {/* Center: Real-Time State Indicator */}
        <div className="hidden md:flex items-center gap-3">
          <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-mono font-semibold tracking-wider ${badge.bg} backdrop-blur-md shadow-inner`}>
            <Activity className={`w-3.5 h-3.5 ${badge.pulse ? 'animate-spin' : ''}`} />
            <span>STATE: {badge.label}</span>
          </div>
        </div>

        {/* Right: Telemetry Controls & System Badges */}
        <div className="flex items-center gap-2 sm:gap-4">
          {/* Backend Status */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <span className={`w-2 h-2 rounded-full ${backendHealth ? 'bg-emerald-400' : 'bg-rose-500 animate-pulse'}`} />
            <span>API: {backendHealth ? '8000 OK' : 'OFFLINE'}</span>
          </div>

          {/* WebSocket Status */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
            <Wifi className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400' : 'text-slate-500'}`} />
            <span>WS: {wsConnected ? 'LIVE' : 'DISCONNECTED'}</span>
          </div>

          {/* Wake Word Trigger */}
          <button
            onClick={onTriggerWake}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-mono font-medium transition-all active:scale-95 shadow-sm shadow-cyan-500/10"
            title="Trigger Wake Word ('Jarvis')"
          >
            <Mic className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Wake "Jarvis"</span>
          </button>

          {/* Mute Audio Toggle */}
          <button
            onClick={onToggleMute}
            className={`p-2 rounded-lg border transition-all text-xs ${
              isMuted
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
                : 'bg-slate-800/80 border-slate-700/80 text-slate-300 hover:bg-slate-800'
            }`}
            title={isMuted ? 'Unmute Speech Audio' : 'Mute Speech Audio'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
