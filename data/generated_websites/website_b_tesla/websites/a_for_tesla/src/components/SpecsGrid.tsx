import React from 'react';
export const SpecsGrid: React.FC = () => (
  <section id="specsgrid" className="py-20 px-8 bg-neutral-950/85 backdrop-blur-xl text-white font-sans border-b border-red-900/40">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
      <div className="md:col-span-6 space-y-4">
        <div className="text-red-500 font-mono text-xs font-bold tracking-widest uppercase">// VELOCITY SPECSGRID</div>
        <h2 className="text-3xl font-extrabold uppercase tracking-tight">SpecsGrid // Tesla</h2>
        <p className="text-neutral-400 text-sm leading-relaxed">High-performance specifications and engineering details.</p>
      </div>
      <div className="md:col-span-6 border-l border-red-900/50 pl-6 space-y-3 font-mono text-xs text-neutral-300">
        <div>PERFORMANCE INDEX: OPTIMAL</div>
        <div>RESPONSE TIME: IMMEDIATE</div>
      </div>
    </div>
  </section>
);
