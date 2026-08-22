import React from 'react';

export default function Services() {
  return (
    <section className="py-16 px-8 max-w-6xl mx-auto border-b border-slate-800">
      <h2 className="text-3xl font-bold text-cyan-400 mb-4">Services Section</h2>
      <p className="text-slate-300">Modern responsive UI component for Services.</p>
      <div className="mt-6 flex gap-4">
        <button className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded font-semibold text-white">
          Explore Services
        </button>
      </div>
    </section>
  );
}