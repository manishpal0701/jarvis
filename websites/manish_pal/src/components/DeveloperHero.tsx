import React, { useState, useEffect } from 'react';
import { ArrowRight, Sparkles, Cpu, Github, Linkedin, Mail } from 'lucide-react';

export const DeveloperHero: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      setMousePos({
        x: (clientX / innerWidth - 0.5) * 30,
        y: (clientY / innerHeight - 0.5) * 30
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <section className="relative min-h-screen pt-28 pb-16 px-6 bg-[#020617] text-white flex items-center justify-center overflow-hidden border-b border-cyan-500/20">
      <div className="hidden lg:flex fixed left-6 top-1/2 -translate-y-1/2 z-40 flex-col space-y-6 items-center bg-slate-950/80 p-3 rounded-full border border-cyan-500/30 backdrop-blur-md shadow-2xl shadow-cyan-500/10">
        <a href="https://github.com" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Github className="w-5 h-5" />
        </a>
        <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Linkedin className="w-5 h-5" />
        </a>
        <a href="mailto:manish07pa@gmail.com" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Mail className="w-5 h-5" />
        </a>
        <div className="w-px h-12 bg-slate-800 my-2" />
        <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest [writing-mode:vertical-lr] rotate-180">Manish Pal</span>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center w-full relative z-10">
        <div className="lg:col-span-6 text-left space-y-6">
          <div className="inline-flex items-center space-x-3 px-4 py-2 rounded-full bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 text-xs font-mono font-bold tracking-widest uppercase shadow-lg shadow-cyan-500/20">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Developer & Architect</span>
          </div>

          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-black tracking-tighter text-white leading-[0.95] uppercase">
            MANISH PAL
          </h1>

          <p className="text-slate-300 text-lg sm:text-xl max-w-xl leading-relaxed font-normal">
            Official website for Ek 3D animated
          </p>

          <div className="flex flex-wrap items-center gap-5 pt-4">
            <a href="#work" className="bg-gradient-to-r from-cyan-500 via-sky-400 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-black px-8 py-4 rounded-full text-sm uppercase tracking-wider flex items-center space-x-3 shadow-2xl shadow-cyan-500/40 hover:scale-105 active:scale-95 transition-all">
              <span>EXPLORE WORK</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a href="#contact" className="border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 hover:text-white font-bold px-8 py-4 rounded-full text-sm uppercase tracking-wider transition-all bg-slate-900/80 hover:bg-slate-900 shadow-xl backdrop-blur-md">
              CONTACT
            </a>
          </div>
        </div>

        <div className="lg:col-span-6 flex justify-center relative">
          <div className="relative w-full max-w-lg aspect-square flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/30 via-blue-600/20 to-pink-500/30 rounded-full blur-3xl animate-pulse pointer-events-none" />
            <div className="relative w-80 h-96 rounded-3xl bg-slate-900/90 border-2 border-cyan-400/60 shadow-[0_0_50px_rgba(6,182,212,0.4)] backdrop-blur-2xl flex flex-col items-center justify-center p-8 text-center space-y-6 overflow-hidden">
              <div className="relative w-36 h-36 rounded-full bg-gradient-to-br from-cyan-500/20 via-slate-950 to-pink-500/20 border-2 border-cyan-400 flex items-center justify-center shadow-inner shadow-cyan-500/40">
                <Cpu className="w-20 h-20 text-cyan-400 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-black tracking-tight text-white">Manish Pal</h3>
                <p className="text-xs font-mono text-cyan-300 uppercase tracking-widest">Developer & Architect</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
