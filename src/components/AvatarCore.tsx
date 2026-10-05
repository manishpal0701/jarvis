import React from 'react';
import { Sparkles, Cpu, Radio } from 'lucide-react';

interface AvatarCoreProps {
  jarvisState: string;
  isSpeaking: boolean;
  isListening: boolean;
}

export const AvatarCore: React.FC<AvatarCoreProps> = ({
  jarvisState,
  isSpeaking,
  isListening,
}) => {
  const getAvatarTheme = (state: string) => {
    switch (state.toUpperCase()) {
      case 'LISTENING':
        return {
          coreGlow: 'from-cyan-400 via-blue-500 to-indigo-600 shadow-cyan-500/50',
          ringBorder: 'border-cyan-400/60',
          waveColor: 'bg-cyan-400',
          statusText: 'Listening for command...',
        };
      case 'THINKING':
      case 'PROCESSING':
        return {
          coreGlow: 'from-purple-400 via-fuchsia-500 to-indigo-600 shadow-purple-500/50',
          ringBorder: 'border-purple-400/60',
          waveColor: 'bg-purple-400',
          statusText: 'Analyzing intent & memory...',
        };
      case 'EXECUTING':
        return {
          coreGlow: 'from-emerald-400 via-teal-500 to-cyan-600 shadow-emerald-500/50',
          ringBorder: 'border-emerald-400/60',
          waveColor: 'bg-emerald-400',
          statusText: 'Executing code & tools...',
        };
      case 'SPEAKING':
        return {
          coreGlow: 'from-amber-400 via-orange-500 to-yellow-600 shadow-amber-500/50',
          ringBorder: 'border-amber-400/60',
          waveColor: 'bg-amber-400',
          statusText: 'Speaking audio response...',
        };
      case 'ERROR':
        return {
          coreGlow: 'from-rose-500 via-red-600 to-pink-700 shadow-rose-500/50',
          ringBorder: 'border-rose-500/60',
          waveColor: 'bg-rose-500',
          statusText: 'Execution anomaly detected',
        };
      default:
        return {
          coreGlow: 'from-cyan-500 via-blue-600 to-slate-800 shadow-cyan-500/30',
          ringBorder: 'border-cyan-500/30',
          waveColor: 'bg-cyan-400',
          statusText: 'JARVIS Standby Engine',
        };
    }
  };

  const theme = getAvatarTheme(jarvisState);

  return (
    <div className="spatial-glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col items-center justify-center min-h-[340px] border border-cyan-500/20 shadow-2xl">
      {/* Background Cyber Grid */}
      <div className="absolute inset-0 bg-spatial-grid opacity-20 pointer-events-none" />
      <div className="absolute inset-0 bg-cyber-radial pointer-events-none" />

      {/* Holographic Header Tag */}
      <div className="absolute top-4 left-4 flex items-center gap-2 text-xs font-mono text-cyan-400/80 bg-slate-900/60 px-3 py-1 rounded-full border border-cyan-500/20">
        <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
        <span>CYBERNETIC AI CORE</span>
      </div>

      {/* Main Spatial Orb */}
      <div className="relative my-6 flex items-center justify-center">
        {/* Outer Orbiting Ring 1 */}
        <div
          className={`absolute w-56 h-56 rounded-full border border-dashed ${theme.ringBorder} animate-rotate-slow opacity-60`}
        />

        {/* Outer Orbiting Ring 2 */}
        <div
          className={`absolute w-44 h-44 rounded-full border ${theme.ringBorder} animate-spin opacity-40`}
          style={{ animationDuration: '15s', animationDirection: 'reverse' }}
        />

        {/* Pulse Glow Aura */}
        <div
          className={`absolute w-36 h-36 rounded-full bg-gradient-to-r ${theme.coreGlow} blur-2xl opacity-60 animate-breathing-glow`}
        />

        {/* Core Spherical Reactor */}
        <div
          className={`relative w-28 h-28 rounded-full bg-gradient-to-tr ${theme.coreGlow} p-1 shadow-2xl flex items-center justify-center transition-all duration-500 transform hover:scale-105`}
        >
          <div className="w-full h-full rounded-full bg-slate-950/90 backdrop-blur-sm flex flex-col items-center justify-center relative overflow-hidden border border-white/20">
            <Cpu className="w-10 h-10 text-cyan-300 stroke-[1.5] animate-pulse" />
            
            {/* Audio Spectrum Bars Overlay when Speaking */}
            {(isSpeaking || jarvisState.toUpperCase() === 'SPEAKING') && (
              <div className="absolute bottom-2 flex items-center gap-1">
                <span className={`w-1 h-4 ${theme.waveColor} rounded-full animate-bounce`} style={{ animationDelay: '0.1s' }} />
                <span className={`w-1 h-6 ${theme.waveColor} rounded-full animate-bounce`} style={{ animationDelay: '0.2s' }} />
                <span className={`w-1 h-3 ${theme.waveColor} rounded-full animate-bounce`} style={{ animationDelay: '0.3s' }} />
                <span className={`w-1 h-5 ${theme.waveColor} rounded-full animate-bounce`} style={{ animationDelay: '0.15s' }} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Real-time State & Status Text */}
      <div className="text-center z-10">
        <h3 className="text-lg font-bold font-mono text-white tracking-wider">
          {jarvisState.toUpperCase()}
        </h3>
        <p className="text-xs font-mono text-cyan-300/80 mt-1 flex items-center justify-center gap-1.5">
          <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" />
          <span>{theme.statusText}</span>
        </p>
      </div>
    </div>
  );
};
