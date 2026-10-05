import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("   BUILDING MANISH — AI ENGINEER PORTFOLIO E2E   ")
print("==================================================")

t_start = time.perf_counter()

output_dir = os.path.join(os.getcwd(), "websites", "manish_ai_engineer_portfolio")
os.makedirs(os.path.join(output_dir, "src", "components"), exist_ok=True)

# 1. package.json
pkg_json = '''{
  "name": "manish-ai-engineer-portfolio",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.40",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }
}'''

# 2. tsconfig.json
tsconfig = '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}'''

# 3. vite.config.ts
vite_cfg = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  }
})'''

# 4. index.html
index_html = '''<!DOCTYPE html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Manish — AI Engineer & Full-Stack Developer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
  </head>
  <body class="bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''

# 5. src/main.tsx
main_tsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''

# 6. src/index.css
index_css = '''@import "tailwindcss";

@layer base {
  body {
    background-color: #020617;
    color: #f8fafc;
    font-family: 'Inter', system-ui, sans-serif;
  }
}

.glass-panel {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(51, 65, 85, 0.6);
}

.glass-card {
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(30, 41, 59, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(6, 182, 212, 0.5);
  box-shadow: 0 10px 30px -10px rgba(6, 182, 212, 0.2);
  transform: translateY(-4px);
}'''

# 7. src/components/Navbar.tsx
navbar_tsx = '''import React, { useState, useEffect } from 'react';

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
}'''

# 8. src/components/Hero.tsx
hero_tsx = '''import React from 'react';

export default function Hero() {
  return (
    <section id="hero" className="relative pt-36 pb-20 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center justify-between gap-12 overflow-hidden">
      <div className="flex-1 space-y-6 text-left">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-800/50 text-cyan-400 text-xs font-mono tracking-wide shadow-sm">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Available for AI & Software Projects
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
          Building Intelligent <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
            AI Agents & Software
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl font-normal leading-relaxed">
          Hi, I&apos;m <span className="text-white font-semibold">Manish</span>. I specialize in autonomous AI desktop agents, local LLM integration, speech synthesis pipelines, and high-performance cross-platform applications.
        </p>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          <a href="#projects" className="px-6 py-3.5 text-sm font-bold text-slate-950 bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-400 rounded-xl shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-95 transition-all">
            Explore Featured Work &rarr;
          </a>
          <a href="#contact" className="px-6 py-3.5 text-sm font-semibold text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-xl transition-all">
            Let&apos;s Connect
          </a>
        </div>

        <div className="pt-6 flex items-center gap-8 border-t border-slate-800/80 text-slate-400 text-xs font-mono">
          <div>
            <div className="text-xl font-bold text-white font-sans">3+</div>
            <div>Major AI Projects</div>
          </div>
          <div className="h-8 w-px bg-slate-800"></div>
          <div>
            <div className="text-xl font-bold text-white font-sans">100%</div>
            <div>Local LLM & Voice</div>
          </div>
          <div className="h-8 w-px bg-slate-800"></div>
          <div>
            <div className="text-xl font-bold text-white font-sans">Flutter</div>
            <div>Cross-Platform</div>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full max-w-lg lg:max-w-none">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-2xl relative group">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
            </div>
            <span className="text-xs font-mono text-slate-400">jarvis_orchestrator.py</span>
          </div>
          <pre className="font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto p-2">
            <code>
<span className="text-purple-400">class</span> <span className="text-cyan-300">JarvisEngine</span>:
    <span className="text-purple-400">def</span> <span className="text-blue-400">__init__</span>(<span className="text-slate-400">self</span>):
        <span className="text-slate-400">self</span>.model = <span className="text-emerald-300">&quot;qwen3:4b-instruct&quot;</span>
        <span className="text-slate-400">self</span>.voice = <span className="text-emerald-300">&quot;PyTTSx3Offline&quot;</span>

    <span className="text-purple-400">async def</span> <span className="text-blue-400">process_voice_cmd</span>(<span className="text-slate-400">self</span>, audio_input):
        intent = <span className="text-slate-400">self</span>.classify(audio_input)
        <span className="text-purple-400">return await</span> <span className="text-slate-400">self</span>.execute(intent)
            </code>
          </pre>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-cyan-400 font-mono">
            <span>⚡ Ollama Local Stream Active</span>
            <span>2.62s Latency</span>
          </div>
        </div>
      </div>
    </section>
  );
}'''

# 9. src/components/About.tsx
about_tsx = '''import React from 'react';

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
}'''

# 10. src/components/Skills.tsx
skills_tsx = '''import React from 'react';

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
}'''

# 11. src/components/Projects.tsx
projects_tsx = '''import React from 'react';

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
}'''

# 12. src/components/Experience.tsx
experience_tsx = '''import React from 'react';

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
}'''

# 13. src/components/Contact.tsx
contact_tsx = '''import React, { useState } from 'react';

export default function Contact() {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <section id="contact" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-800/60">
      <div className="max-w-3xl mx-auto text-center space-y-4 mb-12">
        <div className="inline-block px-3 py-1 rounded-md bg-cyan-950/60 text-cyan-400 text-xs font-mono font-semibold">
          LET&apos;S CONNECT
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Get In Touch
        </h2>
        <p className="text-slate-400 text-sm">
          Have a project in mind or interested in collaborating on AI tools? Send a message!
        </p>
      </div>

      <div className="max-w-xl mx-auto glass-panel p-8 rounded-2xl border border-slate-800">
        {submitted ? (
          <div className="text-center py-8 space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto text-xl font-bold">✓</div>
            <h3 className="text-lg font-bold text-white">Message Sent Successfully!</h3>
            <p className="text-xs text-slate-300">Thank you for reaching out. I will get back to you soon.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5 text-left">
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5">YOUR NAME</label>
              <input required type="text" placeholder="John Doe" className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5">EMAIL ADDRESS</label>
              <input required type="email" placeholder="john@example.com" className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5">MESSAGE</label>
              <textarea required rows={4} placeholder="Hi Manish, I'd like to discuss a project..." className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"></textarea>
            </div>
            <button type="submit" className="w-full py-3.5 px-6 rounded-xl font-bold text-sm text-slate-950 bg-gradient-to-r from-cyan-400 to-teal-400 hover:from-cyan-300 hover:to-teal-300 transition-all shadow-lg shadow-cyan-500/20">
              Send Message &rarr;
            </button>
          </form>
        )}
      </div>
    </section>
  );
}'''

# 14. src/components/Footer.tsx
footer_tsx = '''import React from 'react';

export default function Footer() {
  return (
    <footer className="py-8 px-6 max-w-7xl mx-auto border-t border-slate-800/80 text-center sm:text-left flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
      <div>
        &copy; {new Date().getFullYear()} Manish. All rights reserved.
      </div>
      <div className="flex items-center gap-6">
        <a href="#hero" className="hover:text-cyan-400 transition-colors">Back to top &uarr;</a>
      </div>
    </footer>
  );
}'''

# 15. src/App.tsx
app_tsx = '''import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import About from './components/About';
import Skills from './components/Skills';
import Projects from './components/Projects';
import Experience from './components/Experience';
import Contact from './components/Contact';
import Footer from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-cyan-500 selection:text-slate-950">
      <Navbar />
      <main>
        <Hero />
        <About />
        <Skills />
        <Projects />
        <Experience />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}'''

files_dict = {
  "package.json": pkg_json,
  "tsconfig.json": tsconfig,
  "vite.config.ts": vite_cfg,
  "index.html": index_html,
  "src/main.tsx": main_tsx,
  "src/index.css": index_css,
  "src/components/Navbar.tsx": navbar_tsx,
  "src/components/Hero.tsx": hero_tsx,
  "src/components/About.tsx": about_tsx,
  "src/components/Skills.tsx": skills_tsx,
  "src/components/Projects.tsx": projects_tsx,
  "src/components/Experience.tsx": experience_tsx,
  "src/components/Contact.tsx": contact_tsx,
  "src/components/Footer.tsx": footer_tsx,
  "src/App.tsx": app_tsx,
}

from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()

for rel_p, content in files_dict.items():
    ws.write_workspace_file(output_dir, rel_p, content)

print(f"\n[FILES PERSISTED] {len(files_dict)} project files written to disk.")

# Production Build Gate
from tools.coding.website_deployer import LocalPreviewDeployer
print("\n[RUNNING PRODUCTION BUILD GATE]")
is_built, build_msg = LocalPreviewDeployer.execute_production_build(output_dir)
print(f"Production Build Status: {'SUCCESS' if is_built else 'FAILED'}")

# Preview Server Launch
from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
url, port = server.start_preview(output_dir, port=5174, open_browser=False)

t_total = time.perf_counter() - t_start

print(f"\n==================================================")
print(f"   MANISH PORTFOLIO E2E BUILD COMPLETE           ")
print(f"==================================================")
print(f"Preview URL: {url}")
print(f"Build Result: {'PASS' if is_built else 'FAIL'}")
print(f"Total Time: {t_total:.2f}s")
