import React from 'react';

export default function Skills() {
  const skills = [
    { name: "Python", category: "AI & Automation", level: "Expert", color: "from-blue-500 to-cyan-500" },
    { name: "TypeScript / React", category: "Frontend Architect", level: "Advanced", color: "from-cyan-400 to-teal-400" },
    { name: "Ollama & Local LLMs", category: "AI Infrastructure", level: "Expert", color: "from-purple-500 to-indigo-500" },
    { name: "Flutter / Dart", category: "Mobile Apps", level: "Advanced", color: "from-teal-400 to-emerald-400" },
    { name: "Tailwind CSS v4", category: "Styling & UI Systems", level: "Expert", color: "from-indigo-400 to-blue-500" },
    { name: "OpenCV & Vision", category: "Computer Vision", level: "Intermediate", color: "from-amber-400 to-orange-500" }
  ];

  return (
    <section id="skills" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="text-center max-w-3xl mx-auto space-y-4 mb-14">
        <div className="inline-block px-3 py-1 rounded-md bg-cyan-950/60 text-cyan-400 text-xs font-mono font-semibold">
          TECHNICAL STACK
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Tools & Technologies I Work With
        </h2>
        <p className="text-slate-400 text-sm">
          A curated ecosystem of frameworks and tools powering production applications.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {skills.map((skill, idx) => (
          <div key={idx} className="glass-card p-6 rounded-2xl text-left relative overflow-hidden group">
            <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${skill.color}`}></div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">{skill.name}</h3>
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">{skill.level}</span>
            </div>
            <p className="text-xs text-slate-400 font-mono">{skill.category}</p>
          </div>
        ))}
      </div>
    </section>
  );
}