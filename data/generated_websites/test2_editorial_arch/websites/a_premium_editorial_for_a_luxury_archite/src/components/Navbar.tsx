import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-[#1a0933]/90 border-b border-purple-800/50 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="text-coral-400 font-black text-2xl tracking-wider text-white">A Luxury Architecture Studio</div>
      <div className="hidden md:flex space-x-8 text-sm font-bold text-purple-200">
        <a href="#about" className="hover:text-pink-400">Manifesto</a>
        <a href="#services" className="hover:text-pink-400">Showcase</a>
        <a href="#contact" className="hover:text-pink-400">Collab</a>
      </div>
      <a href="#contact" className="bg-gradient-to-r from-pink-500 to-purple-600 text-white font-bold text-sm px-5 py-2.5 rounded-xl">
        Let's Create
      </a>
    </div>
  </nav>
);
