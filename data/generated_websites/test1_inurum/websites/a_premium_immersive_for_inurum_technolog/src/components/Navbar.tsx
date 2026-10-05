import React from 'react';
import { Sparkles } from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/85 border-b border-slate-800 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Sparkles className="w-5 h-5 text-cyan-400" />
        <span className="font-extrabold text-xl text-white tracking-tight">Inurum Technology</span>
      </div>
      <div className="hidden lg:flex space-x-8 text-sm font-medium text-slate-300">
        <a href="#about" className="hover:text-cyan-400">About</a>
        <a href="#services" className="hover:text-cyan-400">Capabilities</a>
        <a href="#projects" className="hover:text-cyan-400">Work</a>
        <a href="#contact" className="hover:text-cyan-400">Contact</a>
      </div>
      <a href="#contact" className="bg-cyan-500 text-slate-950 px-5 py-2 rounded-xl font-bold text-sm">
        Connect
      </a>
    </div>
  </nav>
);
