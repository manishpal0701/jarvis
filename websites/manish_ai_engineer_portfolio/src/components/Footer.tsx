import React from 'react';

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
}