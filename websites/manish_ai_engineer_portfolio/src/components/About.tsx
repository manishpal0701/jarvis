import React from 'react';

export default function About() {
  return (
    <section id="about" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="flex flex-col md:flex-row items-center gap-12">
        <div className="w-full md:w-1/3 flex justify-center">
          <div className="relative group">
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-cyan-500 to-indigo-600 blur opacity-40 group-hover:opacity-75 transition duration-500"></div>
            <img 
              src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80" 
              alt="Manish Profile" 
              className="relative w-64 h-64 sm:w-72 sm:h-72 object-cover rounded-2xl border border-slate-700 shadow-2xl"
            />
          </div>
        </div>

        <div className="w-full md:w-2/3 space-y-6 text-left">
          <div className="inline-block px-3 py-1 rounded-md bg-cyan-950/60 text-cyan-400 text-xs font-mono font-semibold">
            ABOUT ME
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Passionate About Autonomous Systems & Modern Web Design
          </h2>
          <p className="text-slate-300 leading-relaxed text-base">
            I am a full-stack engineer and AI specialist dedicated to crafting seamless software solutions. My core focus lies in engineering local LLM pipelines, multimodal computer vision applications, desktop automation systems, and responsive modern web experiences.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="glass-card p-4 rounded-xl">
              <h3 className="text-white font-bold text-sm mb-1">🤖 AI & LLM Systems</h3>
              <p className="text-slate-400 text-xs">Ollama, Qwen3, PyTTSx3 voice coordinator, state machines.</p>
            </div>
            <div className="glass-card p-4 rounded-xl">
              <h3 className="text-white font-bold text-sm mb-1">💻 Full-Stack Development</h3>
              <p className="text-slate-400 text-xs">React, TypeScript, Tailwind CSS, Python backend, Vite.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}