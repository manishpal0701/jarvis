import React from 'react';
import { Sparkles } from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-emerald-950/80 backdrop-blur-xl border-b border-emerald-800/50 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Sparkles className="w-6 h-6 text-emerald-400" />
        <span className="font-extrabold text-xl text-emerald-50">Inurum Technology</span>
      </div>
      <div className="hidden md:flex space-x-8 text-sm font-medium text-emerald-200">
        <a href="#about" className="hover:text-emerald-400">About</a>
        <a href="#services" className="hover:text-emerald-400">Capabilities</a>
        <a href="#contact" className="hover:text-emerald-400">Contact</a>
      </div>
      <a href="#contact" className="bg-emerald-500 hover:bg-emerald-400 text-emerald-950 px-5 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-emerald-500/20">
        Get Started
      </a>
    </div>
  </nav>
);
