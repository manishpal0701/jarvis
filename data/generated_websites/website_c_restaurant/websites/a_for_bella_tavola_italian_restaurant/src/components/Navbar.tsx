import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-stone-950/90 border-b border-amber-900/40 px-8 py-5 flex items-center justify-between font-serif">
    <div className="text-amber-400 font-extrabold text-2xl tracking-wide">Bella Tavola Italian Restaurant</div>
    <div className="hidden md:flex space-x-8 text-xs font-sans tracking-widest uppercase text-stone-300">
      <a href="#about" className="hover:text-amber-400">Story</a>
      <a href="#services" className="hover:text-amber-400">Services</a>
      <a href="#contact" className="hover:text-amber-400">Reserve</a>
    </div>
    <a href="#contact" className="border border-amber-500/60 text-amber-400 hover:bg-amber-500 hover:text-stone-950 font-sans text-xs px-6 py-2.5 uppercase font-bold tracking-widest transition-colors">
      Inquire
    </a>
  </nav>
);
