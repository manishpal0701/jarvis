import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export const FeaturedProjects: React.FC = () => (
  <section id="projects" className="relative py-32 px-6 bg-slate-950/50 backdrop-blur-md text-white border-t border-white/10 z-10">
    <div className="max-w-5xl mx-auto space-y-16">
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.3em]">02 // SELECTED WORKS</span>
          <h2 className="text-4xl sm:text-6xl font-light text-white tracking-widest uppercase mt-2">PROJECTS</h2>
        </div>
        <p className="text-xs font-mono text-slate-400 max-w-xs">Selected interactive web experiences and spatial applications by Manish Pal.</p>
      </div>

      <div className="space-y-10">
        <div className="group border border-white/10 hover:border-cyan-400/50 p-8 sm:p-12 rounded-2xl bg-white/5 backdrop-blur-xl transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">[ PROJECT 01 // 2026 ]</span>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="text-3xl font-light tracking-wider text-white mt-4 group-hover:text-cyan-300 transition-colors">Spatial Interactive Environment</h3>
          <p className="text-xs font-mono text-slate-400 mt-3 max-w-2xl leading-relaxed">3D canvas landscape featuring interactive procedural mesh wireframes, camera z-translation on scroll, and frosted glass UI elements.</p>
        </div>

        <div className="group border border-white/10 hover:border-emerald-400/50 p-8 sm:p-12 rounded-2xl bg-white/5 backdrop-blur-xl transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">[ PROJECT 02 // 2025 ]</span>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </div>
          <h3 className="text-3xl font-light tracking-wider text-white mt-4 group-hover:text-emerald-300 transition-colors">Editorial Digital System</h3>
          <p className="text-xs font-mono text-slate-400 mt-3 max-w-2xl leading-relaxed">Minimalist editorial publication framework featuring extended letter tracking, micro-labels, and fluid typography scale.</p>
        </div>
      </div>
    </div>
  </section>
);
