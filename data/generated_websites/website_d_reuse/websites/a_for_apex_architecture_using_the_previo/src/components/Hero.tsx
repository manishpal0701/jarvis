import React from 'react';
import { ArrowDownRight } from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-24 px-8 bg-slate-50 border-b border-slate-300 min-h-[80vh] flex flex-col justify-between">
    <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
      <div className="lg:col-span-8 space-y-8 text-left">
        <div className="text-xs font-mono text-blue-600 tracking-widest uppercase font-bold">[ SWISS EDITORIAL ARCHITECTURE ]</div>
        <h1 className="text-5xl sm:text-7xl font-extrabold text-slate-950 tracking-tighter leading-none">
          Structural Engineering & Design Direction for Apex Architecture Using The Previous Website'S Exact Design.
        </h1>
        <p className="text-slate-600 text-lg max-w-2xl font-normal leading-relaxed">
          Apex Architecture Using The Previous Website'S Exact Design applies strict architectural principles, modular component hierarchy, and functional clarity to complex web systems.
        </p>
        <div className="pt-4 flex items-center space-x-4 font-mono text-sm">
          <a href="#projects" className="bg-slate-950 text-white px-8 py-4 uppercase font-bold hover:bg-blue-600 transition-colors flex items-center space-x-2">
            <span>Explore Works</span>
            <ArrowDownRight className="w-4 h-4" />
          </a>
        </div>
      </div>
      <div className="lg:col-span-4 border-l border-slate-300 pl-8 space-y-6 text-slate-700 text-xs font-mono">
        <div><span className="text-slate-400">FOUNDED //</span> Apex Architecture Using The Previous Website'S Exact Design</div>
        <div><span className="text-slate-400">DISCIPLINE //</span> Architectural Software & Systems</div>
        <div><span className="text-slate-400">METHODOLOGY //</span> Grid Order & Asymmetric Columns</div>
      </div>
    </div>
  </section>
);
