import React, { useEffect, useState } from 'react';

/**
 * Family F — Automotive Cinematic Environment
 * Deep pitch black & electric red velocity theme with light streaks and perspective light trails.
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
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-neutral-950">
      {/* 1. Velocity Red Light Streaks */}
      <div 
        className="absolute inset-0 opacity-60"
        style={{
          background: `radial-gradient(ellipse at 50% 100%, rgba(232, 33, 39, 0.25) 0%, rgba(153, 27, 27, 0.1) 60%, rgba(12, 12, 14, 0.98) 100%)`
        }}
      />
      {/* 2. Horizontal Speed Parallax Lines */}
      <div 
        className="absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-red-600/50 to-transparent animate-pulse-glow"
        style={{ top: `${(scrollProgress * 150) % 100}%` }}
      />
      <div 
        className="absolute inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-red-500/30 to-transparent"
        style={{ top: `${((scrollProgress * 150) + 40) % 100}%` }}
      />
      {/* 3. Dramatic Lighting Backdrop */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[400px] bg-red-600/10 blur-[140px] pointer-events-none" />
    </div>
  );
};
export default DynamicSpatialEnvironment;
