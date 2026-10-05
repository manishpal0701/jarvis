import React from 'react';
import { Sparkles, Github, Linkedin, Mail, Twitter } from 'lucide-react';
export const Navbar: React.FC = () => (
  <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-slate-950/70 backdrop-blur-xl border-b border-cyan-500/20 text-white flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center shadow-lg shadow-cyan-500/20">
        <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
      </div>
      <span className="font-black text-xl tracking-tight text-white">Manish Pal</span>
    </div>

    <nav className="hidden md:flex items-center space-x-8 text-xs font-mono font-bold uppercase tracking-widest text-slate-300">
      <a href="#about" className="hover:text-cyan-400 transition-colors">About</a>
      <a href="#services" className="hover:text-cyan-400 transition-colors">Services</a>
      <a href="#work" className="hover:text-cyan-400 transition-colors">Work</a>
      <a href="#skills" className="hover:text-cyan-400 transition-colors">Skills</a>
      <a href="#contact" className="hover:text-cyan-400 transition-colors">Contact</a>
    </nav>

    <div className="flex items-center space-x-4">
      <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-[10px] font-mono text-cyan-300 font-bold">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <span>Available</span>
      </div>
      <a href="#contact" className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-xs tracking-wider uppercase shadow-lg shadow-cyan-500/30 transition-all hover:scale-105 active:scale-95">
        GET IN TOUCH
      </a>
    </div>
  </header>
);