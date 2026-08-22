import React, { useState } from 'react';

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
}