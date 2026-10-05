import React, { useEffect, useState } from 'react';

/**
 * Family B — Swiss Editorial Environment
 * Strict architectural grid lines, light neutral canvas, thin rules, minimal motion.
 * ABSOLUTELY NO futuristic cyan glows, particles, or neon lighting.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      const progress = totalScroll > 0 ? window.scrollY / totalScroll : 0;
      setScrollProgress(progress);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-slate-50">
      {/* 1. Structural Architectural Grid Lines */}
      <div 
        className="absolute inset-0 opacity-15"
        style={{
          backgroundImage: `linear-gradient(to right, #0f172a 1px, transparent 1px), linear-gradient(to bottom, #0f172a 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
          transform: `translateY(${scrollProgress * -30}px)`
        }}
      />
      {/* 2. Thin Asymmetric Boundary Rule */}
      <div className="absolute top-0 left-24 bottom-0 w-[1px] bg-slate-300" />
      <div className="absolute top-0 right-24 bottom-0 w-[1px] bg-slate-300" />
      {/* 3. Minimal Corner Blueprint Indicator */}
      <div className="absolute top-8 left-8 text-[10px] font-mono text-slate-400 tracking-widest uppercase">
        SWISS EDITORIAL ARCHITECTURE // GRID SYSTEM 80px
      </div>
    </div>
  );
};
export default DynamicSpatialEnvironment;
