import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-slate-50 border-b border-slate-300 px-8 py-5 flex items-center justify-between font-sans">
    <div className="font-extrabold text-2xl tracking-tighter text-slate-900">APEX ARCHITECTURE USING EXACTLY THE VISUAL DESIGN AND INTERACTION ARCHITECTURE OF TEST 2</div>
    <div className="hidden md:flex space-x-8 text-xs font-mono tracking-wider uppercase text-slate-600">
      <a href="#about" className="hover:text-blue-600">01 // About</a>
      <a href="#services" className="hover:text-blue-600">02 // Capabilities</a>
      <a href="#projects" className="hover:text-blue-600">03 // Work</a>
      <a href="#contact" className="hover:text-blue-600">04 // Contact</a>
    </div>
    <a href="#contact" className="bg-blue-600 hover:bg-blue-700 text-white font-mono text-xs px-5 py-2.5 uppercase font-bold tracking-wider">
      Inquire Now
    </a>
  </nav>
);
