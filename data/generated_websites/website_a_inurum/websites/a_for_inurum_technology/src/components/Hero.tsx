import React from 'react';
import { ArrowRight, Feather } from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-28 px-6 bg-emerald-950 text-emerald-50 min-h-[80vh] flex items-center justify-center text-center perspective-1000">
    <div className="max-w-4xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-flex items-center space-x-2 bg-emerald-900/60 border border-emerald-700/60 px-4 py-1.5 rounded-full text-emerald-300 text-xs font-semibold RotatingCore">
        <Feather className="w-4 h-4 text-emerald-400" />
        <span>ORGANIC DIGITAL ECOSYSTEM</span>
      </div>
      <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
        Fluid Intelligence & Continuous Transformation with Inurum Technology.
      </h1>
      <p className="text-emerald-200/90 text-lg leading-relaxed max-w-2xl mx-auto">
        Inurum Technology builds soft, adaptable digital systems that continuously transform alongside business dynamics.
      </p>
      <div>
        <a href="#contact" className="inline-flex items-center space-x-2 bg-emerald-400 hover:bg-emerald-300 text-emerald-950 font-bold px-8 py-4 rounded-full text-base shadow-xl shadow-emerald-500/20">
          <span>Explore Ecosystem</span>
          <ArrowRight className="w-5 h-5" />
        </a>
      </div>
    </div>
  </section>
);
