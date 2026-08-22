import React from 'react';

export default function Experience() {
  const experiences = [
    {
      role: "Lead AI Engineer & System Architect",
      period: "2024 — Present",
      organization: "Jarvis AI Ecosystem",
      desc: "Architected modular desktop assistant state machine, custom offline PyTTSx3 voice synthesis provider, local Ollama LLM intent router, and live streaming workspace."
    },
    {
      role: "Full-Stack Developer",
      period: "2023 — 2024",
      organization: "Independent Projects",
      desc: "Engineered responsive web applications using React, TypeScript, Tailwind CSS, Vite, and Python automation tools."
    }
  ];

  return (
    <section id="experience" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="text-center max-w-3xl mx-auto space-y-4 mb-14">
        <div className="inline-block px-3 py-1 rounded-md bg-cyan-950/60 text-cyan-400 text-xs font-mono font-semibold">
          CAREER TIMELINE
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Experience & Achievements
        </h2>
      </div>

      <div className="max-w-3xl mx-auto space-y-6">
        {experiences.map((exp, idx) => (
          <div key={idx} className="glass-card p-6 rounded-2xl text-left border-l-4 border-l-cyan-500">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
              <h3 className="text-lg font-bold text-white">{exp.role}</h3>
              <span className="text-xs font-mono text-cyan-400">{exp.period}</span>
            </div>
            <div className="text-xs font-semibold text-slate-300 mb-3">{exp.organization}</div>
            <p className="text-slate-300 text-xs leading-relaxed">{exp.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}