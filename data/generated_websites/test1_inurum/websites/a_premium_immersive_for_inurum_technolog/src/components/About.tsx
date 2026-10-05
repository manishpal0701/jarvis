import React from 'react';
export const About: React.FC = () => (
  <section id="about" className="py-20 px-6 bg-slate-950/80 backdrop-blur-xl text-white border-t border-slate-900/80">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
      <div className="md:col-span-8 space-y-4">
        <span className="text-xs font-mono text-cyan-400 uppercase font-semibold">SPATIAL COMPONENT // ABOUT</span>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">About — Inurum Technology</h2>
        <p className="text-slate-300 text-base leading-relaxed">Spatial depth layering and glassmorphic composition.</p>
      </div>
    </div>
  </section>
);
