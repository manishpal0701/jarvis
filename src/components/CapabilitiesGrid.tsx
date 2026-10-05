import React from 'react';
import { Code2, TrendingUp, UserCheck, Monitor, Brain, CloudSun } from 'lucide-react';

interface CapabilitiesGridProps {
  onSelectCommand: (cmd: string) => void;
}

export const CapabilitiesGrid: React.FC<CapabilitiesGridProps> = ({ onSelectCommand }) => {
  const capabilities = [
    {
      icon: Code2,
      title: 'Code Assistant & Builder',
      desc: 'React, Next.js, Flutter & Python generation',
      cmd: 'Jarvis, ek simple Python file banao.',
      badge: 'PROD READY',
      color: 'text-cyan-400 border-cyan-500/30 bg-cyan-950/30',
    },
    {
      icon: TrendingUp,
      title: 'Stock Market Analyzer',
      desc: 'Multi-timeframe technical indicator analysis',
      cmd: 'Check stock price of TSLA',
      badge: 'FINANCE',
      color: 'text-emerald-400 border-emerald-500/30 bg-emerald-950/30',
    },
    {
      icon: UserCheck,
      title: 'Face Recognition & Vision',
      desc: 'ArcFace biometric camera verification',
      cmd: 'Who is in front of camera',
      badge: 'VISION',
      color: 'text-purple-400 border-purple-500/30 bg-purple-950/30',
    },
    {
      icon: Monitor,
      title: 'Computer Automation',
      desc: 'App launcher, system sleep & desktop control',
      cmd: 'System status update',
      badge: 'SYSTEM',
      color: 'text-amber-400 border-amber-500/30 bg-amber-950/30',
    },
    {
      icon: Brain,
      title: 'Memory Subsystem',
      desc: 'Persistent facts, preferences & recall',
      cmd: 'What do you remember about me?',
      badge: 'MEMORY',
      color: 'text-blue-400 border-blue-500/30 bg-blue-950/30',
    },
    {
      icon: CloudSun,
      title: 'Weather & Environment',
      desc: 'Real-time weather lookup & monitor',
      cmd: 'What is the weather today?',
      badge: 'MONITOR',
      color: 'text-indigo-400 border-indigo-500/30 bg-indigo-950/30',
    },
  ];

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <h2 className="text-sm font-bold font-mono text-white tracking-wide flex items-center gap-2">
          <span>JARVIS SYSTEM CAPABILITIES</span>
        </h2>
        <span className="text-[10px] font-mono text-slate-400">6 ACTIVE MODULES</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {capabilities.map((cap, idx) => {
          const Icon = cap.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectCommand(cap.cmd)}
              className="text-left p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/40 transition-all card-3d-tilt group relative overflow-hidden flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-2 rounded-lg border ${cap.color}`}>
                    <Icon className="w-4 h-4 stroke-[2]" />
                  </div>
                  <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400 group-hover:border-cyan-500/50 group-hover:text-cyan-400 transition-colors">
                    {cap.badge}
                  </span>
                </div>
                <h3 className="text-xs font-bold font-mono text-slate-100 group-hover:text-cyan-300 transition-colors">
                  {cap.title}
                </h3>
                <p className="text-[11px] font-sans text-slate-400 mt-1 leading-snug">
                  {cap.desc}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-cyan-400/80 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Run capability</span>
                <span>→</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
