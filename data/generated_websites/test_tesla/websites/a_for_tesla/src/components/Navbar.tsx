import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-neutral-950 border-b border-red-900/50 px-8 py-4 flex items-center justify-between">
    <div className="text-white font-extrabold text-2xl tracking-tighter flex items-center space-x-2">
      <span className="w-3 h-3 bg-red-600 inline-block" />
      <span>TESLA</span>
    </div>
    <div className="hidden md:flex space-x-8 text-xs font-mono text-neutral-300 tracking-widest uppercase">
      <a href="#about" className="hover:text-red-500">Performance</a>
      <a href="#services" className="hover:text-red-500">Engineering</a>
      <a href="#contact" className="hover:text-red-500">Contact</a>
    </div>
    <a href="#contact" className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs uppercase px-5 py-2.5 tracking-wider">
      Test Drive
    </a>
  </nav>
);
