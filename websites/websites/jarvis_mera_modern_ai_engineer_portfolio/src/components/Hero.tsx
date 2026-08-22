import React from 'react';

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
}