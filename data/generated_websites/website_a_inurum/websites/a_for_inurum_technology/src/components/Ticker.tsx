import React from 'react';
export const Ticker: React.FC = () => (
  <section id="ticker" className="py-20 px-6 bg-black/85 backdrop-blur-md text-white border-b-4 border-[#333] font-mono">
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="inline-block bg-[#ccff00] text-black font-black text-xs px-3 py-1 uppercase">
        RAW BLOCK // TICKER
      </div>
      <h2 className="text-4xl sm:text-5xl font-black text-white uppercase tracking-tight leading-none">
        Ticker ENGINE BY <span className="text-[#ccff00]">Inurum Technology</span>.
      </h2>
      <p className="text-slate-300 text-lg max-w-2xl">
        Uncompromised brutalist structure with high contrast borders and direct execution.
      </p>
    </div>
  </section>
);
