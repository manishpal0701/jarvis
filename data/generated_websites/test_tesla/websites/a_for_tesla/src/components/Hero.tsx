import React from 'react';
import { Zap } from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-28 px-8 bg-neutral-950 text-white min-h-[85vh] flex flex-col justify-center perspective-1000">
    <div className="max-w-6xl mx-auto space-y-8 text-left card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-flex items-center space-x-2 text-red-500 font-mono text-xs font-bold tracking-widest uppercase RotatingCore">
        <Zap className="w-4 h-4" />
        <span>AUTOMOTIVE CINEMATIC VELOCITY</span>
      </div>
      <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight leading-none uppercase">
        HIGH PERFORMANCE ENGINEERING BY <span className="text-red-600">Tesla</span>.
      </h1>
      <p className="text-neutral-400 text-lg max-w-2xl leading-relaxed">
        Speed, precision, and low-key cinematic lighting. Tesla delivers high-velocity digital capabilities.
      </p>
      <div>
        <a href="#contact" className="bg-red-600 hover:bg-red-700 text-white font-extrabold text-sm uppercase px-8 py-4 inline-block tracking-wider">
          Explore Specifications
        </a>
      </div>
    </div>
  </section>
);
