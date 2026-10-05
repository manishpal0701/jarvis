import React from 'react';
import { ArrowRight, Cpu, Sparkles } from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="relative min-h-[85vh] pt-24 pb-28 px-6 bg-slate-950 text-white flex items-center justify-center perspective-1000">
    <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full card-3d-tilt glass-panel">
      <div className="lg:col-span-7 text-left space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-semibold">
          <span>SPATIAL INTELLIGENCE // INURUM TECHNOLOGY</span>
        </div>
        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
          Supercharge Your Workflow: Architecting Spatial Systems & Cloud Infrastructure.
        </h1>
        <p className="text-slate-300 text-lg max-w-2xl leading-relaxed">
          Inurum Technology delivers high-performance digital platforms with 3D spatial depth.
        </p>
        <div className="flex items-center space-x-4">
          <a href="#contact" className="bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 font-bold px-8 py-4 rounded-xl text-base flex items-center space-x-2">
            <span>Explore Solutions</span>
            <ArrowRight className="w-5 h-5" />
          </a>
        </div>
      </div>
      <div className="lg:col-span-5 flex items-center justify-center">
        <div className="w-64 h-64 rounded-3xl bg-slate-900 border border-cyan-500/30 p-6 flex flex-col items-center justify-center text-center space-y-4 animate-float-slow">
          <Sparkles className="w-12 h-12 text-cyan-400" />
          <div className="font-bold text-white font-mono">INURUM TECHNOLOGY-CORE</div>
          <div className="text-xs text-cyan-300 font-mono">SPATIAL ONLINE</div>
        </div>
      </div>
    </div>
  </section>
);
