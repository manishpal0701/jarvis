import React, { useState, useEffect } from 'react';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[92%] max-w-6xl transition-all duration-300 ${scrolled ? 'glass-panel shadow-2xl shadow-cyan-950/20' : 'bg-slate-900/40 backdrop-blur-md border border-slate-800/50'} rounded-full px-6 py-3.5 flex items-center justify-between`}>
      <a href="#hero" className="flex items-center gap-2 text-lg font-bold tracking-tight text-white group">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-slate-950 font-extrabold text-sm shadow-md shadow-cyan-500/20 group-hover:scale-105 transition-transform">
          M
        </div>
        <span>MANISH<span className="text-cyan-400">.AI</span></span>
      </a>

      <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
        <a href="#about" className="hover:text-cyan-400 transition-colors">About</a>
        <a href="#skills" className="hover:text-cyan-400 transition-colors">Skills</a>
        <a href="#projects" className="hover:text-cyan-400 transition-colors">Projects</a>
        <a href="#experience" className="hover:text-cyan-400 transition-colors">Experience</a>
        <a href="#contact" className="hover:text-cyan-400 transition-colors">Contact</a>
      </nav>

      <div className="flex items-center gap-3">
        <a href="#contact" className="hidden sm:inline-flex px-4 py-2 text-xs font-semibold tracking-wide text-slate-950 bg-gradient-to-r from-cyan-400 to-teal-400 hover:from-cyan-300 hover:to-teal-300 rounded-full shadow-lg shadow-cyan-500/20 transition-all hover:scale-105">
          Get In Touch
        </a>
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden text-slate-300 hover:text-white p-2">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={mobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="absolute top-16 left-0 right-0 glass-panel rounded-2xl p-6 flex flex-col gap-4 text-center md:hidden border border-slate-800 shadow-2xl">
          <a href="#about" onClick={() => setMobileMenuOpen(false)} className="text-slate-200 hover:text-cyan-400 py-2">About</a>
          <a href="#skills" onClick={() => setMobileMenuOpen(false)} className="text-slate-200 hover:text-cyan-400 py-2">Skills</a>
          <a href="#projects" onClick={() => setMobileMenuOpen(false)} className="text-slate-200 hover:text-cyan-400 py-2">Projects</a>
          <a href="#experience" onClick={() => setMobileMenuOpen(false)} className="text-slate-200 hover:text-cyan-400 py-2">Experience</a>
          <a href="#contact" onClick={() => setMobileMenuOpen(false)} className="text-slate-200 hover:text-cyan-400 py-2">Contact</a>
        </div>
      )}
    </header>
  );
}