import React from 'react';

export default function Projects() {
  const projects = [
    {
      title: "Jarvis AI Assistant",
      subtitle: "Local Voice & Automation Agent",
      description: "An autonomous desktop AI assistant featuring offline PyTTSx3 voice output, Ollama LLM integration, local speech recognition, and system routing.",
      image: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80",
      tags: ["Python", "Ollama", "Qwen3", "PyTTSx3", "StateMachine"]
    },
    {
      title: "AI Video Editing Agent",
      subtitle: "ExtendScript Adobe Premiere Automation",
      description: "Automated video production bridge connecting Python AI reasoning engines directly into Adobe Premiere Pro 2021 CEP panel environment.",
      image: "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80",
      tags: ["Python", "ExtendScript", "Premiere Pro", "CEP"]
    },
    {
      title: "Flutter Attendance Mobile App",
      subtitle: "Cross-Platform Biometric Tracker",
      description: "Mobile application with real-time biometric verification, Firebase sync, automated report generation, and intuitive UI.",
      image: "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=800&q=80",
      tags: ["Flutter", "Dart", "Firebase", "Android"]
    }
  ];

  return (
    <section id="projects" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="text-center max-w-3xl mx-auto space-y-4 mb-14">
        <div className="inline-block px-3 py-1 rounded-md bg-cyan-950/60 text-cyan-400 text-xs font-mono font-semibold">
          FEATURED ENGINEERING
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Recent Projects & Systems
        </h2>
        <p className="text-slate-400 text-sm">
          Real-world applications built for desktop automation, AI intelligence, and mobile experiences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {projects.map((proj, idx) => (
          <div key={idx} className="glass-card rounded-2xl overflow-hidden flex flex-col text-left group">
            <div className="h-48 overflow-hidden relative">
              <img 
                src={proj.image} 
                alt={proj.title} 
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80"></div>
            </div>

            <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
              <div>
                <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider">{proj.subtitle}</span>
                <h3 className="text-xl font-bold text-white mt-1 group-hover:text-cyan-300 transition-colors">{proj.title}</h3>
                <p className="text-slate-300 text-xs leading-relaxed mt-2">{proj.description}</p>
              </div>

              <div className="flex flex-wrap gap-1.5 pt-2">
                {proj.tags.map((t, i) => (
                  <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700/60">{t}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}