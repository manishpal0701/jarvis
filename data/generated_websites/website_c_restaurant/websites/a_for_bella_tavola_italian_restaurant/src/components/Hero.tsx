import React from 'react';
export const Hero: React.FC = () => (
  <section className="py-32 px-8 bg-stone-950 text-stone-100 min-h-[85vh] flex items-center justify-center text-center perspective-1000">
    <div className="max-w-4xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="text-amber-500 text-xs font-mono tracking-widest uppercase font-semibold RotatingCore">
        EDITORIAL LUXURY // bella-tavola-italian-restaurant
      </div>
      <h1 className="text-5xl sm:text-7xl font-serif font-bold text-stone-100 tracking-tight leading-tight">
        Crafted Precision & Timeless Elegance by Bella Tavola Italian Restaurant.
      </h1>
      <p className="text-stone-400 text-lg max-w-2xl mx-auto font-sans leading-relaxed">
        Bella Tavola Italian Restaurant elevates brand presence through high negative space, serif display typography, and tailored digital execution.
      </p>
      <div>
        <a href="#contact" className="inline-block border border-amber-500 bg-amber-500/10 text-amber-300 font-sans text-sm uppercase tracking-widest font-bold px-10 py-4 hover:bg-amber-500 hover:text-stone-950 transition-colors">
          Experience Excellence
        </a>
      </div>
    </div>
  </section>
);
