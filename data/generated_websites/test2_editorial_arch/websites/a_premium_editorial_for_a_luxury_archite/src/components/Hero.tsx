import React from 'react';
export const Hero: React.FC = () => (
  <section className="py-28 px-6 bg-[#1a0933] text-white min-h-[85vh] flex items-center justify-center text-center perspective-1000">
    <div className="max-w-4xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-block bg-pink-500/20 border border-pink-400/40 text-pink-300 text-xs font-mono font-bold px-4 py-1.5 rounded-full RotatingCore">
        EXPRESSIVE CREATIVE AGENCY
      </div>
      <h1 className="text-5xl sm:text-7xl font-black text-white tracking-tight leading-tight">
        Art-Directed Digital Collisions by A Luxury Architecture Studio.
      </h1>
      <p className="text-purple-200 text-lg max-w-2xl mx-auto leading-relaxed">
        A Luxury Architecture Studio breaks conventional SaaS templates with bold typography collisions and expressive color fields.
      </p>
      <div>
        <a href="#contact" className="bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-black text-base px-9 py-4 rounded-xl inline-block shadow-lg shadow-pink-500/20">
          Start Experiment
        </a>
      </div>
    </div>
  </section>
);
