import React from 'react';
export const Services: React.FC = () => (
  <section id="services" className="py-20 px-8 bg-slate-50/90 backdrop-blur-sm border-b border-slate-300 font-sans">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
      <div className="md:col-span-4 border-l-2 border-blue-600 pl-4">
        <span className="text-xs font-mono text-blue-600 font-bold uppercase">[ SERVICES // ARCHITECTURE ]</span>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-2">Services</h2>
      </div>
      <div className="md:col-span-8 space-y-4">
        <p className="text-slate-700 text-base leading-relaxed">
          Tesla engineered this operational services module according to strict grid alignment and architectural proportion.
        </p>
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-200 text-xs font-mono text-slate-600">
          <div>// SPECIFICATION 01: Modular System</div>
          <div>// SPECIFICATION 02: High Density</div>
        </div>
      </div>
    </div>
  </section>
);
