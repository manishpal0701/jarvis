import React, { useEffect, useState } from 'react';

/**
 * Family G — Futuristic Interface Environment
 * Monospace HUD telemetry data grid, scanlines, glowing cyan/purple node streams.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      setScrollProgress(totalScroll > 0 ? window.scrollY / totalScroll : 0);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-slate-950 font-mono">
      {/* 1. HUD Telemetry Grid */}
      <div 
        className="absolute inset-0 bg-spatial-grid opacity-30"
        style={{
          transform: `perspective(1000px) rotateX(20deg) translateY(${scrollProgress * -50}px)`
        }}
      />
      {/* 2. Holographic Energy Ambient Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-cyan-500/15 rounded-full blur-[140px] animate-breathing-glow" />
      {/* 3. CRT Scanline Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400/5 to-transparent h-[4px] animate-pulse-glow" style={{ top: `${(scrollProgress * 200) % 100}%` }} />
      {/* 4. Monospace Telemetry Labels */}
      <div className="absolute bottom-6 left-6 text-[10px] text-cyan-400/60 tracking-widest">
        [SYS_STATUS: ONLINE] [GRID_NODE: ALPHA-7] [LATENCY: 0.8ms]
      </div>
    </div>
  );
};
export default DynamicSpatialEnvironment;
