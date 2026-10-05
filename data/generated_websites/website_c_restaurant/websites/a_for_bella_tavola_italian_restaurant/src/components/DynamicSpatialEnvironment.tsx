import React, { useEffect, useState } from 'react';

/**
 * Family E — Editorial Luxury Environment
 * Deep mahogany & warm stone background, candlelit gold foil ambience, minimal gold line accents.
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
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-stone-950">
      {/* 1. Warm Candlelit Amber Radial Glow */}
      <div 
        className="absolute inset-0 opacity-80 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at 50% ${30 + scrollProgress * 40}%, rgba(245, 158, 11, 0.18) 0%, rgba(120, 53, 15, 0.15) 50%, rgba(12, 10, 9, 0.95) 100%)`
        }}
      />
      {/* 2. Floating Gold Foil Geometry */}
      <div 
        className="absolute top-1/3 right-16 w-64 h-64 border border-amber-500/20 rounded-full opacity-40 animate-float-slow"
        style={{ transform: `translateY(${scrollProgress * -40}px) rotate(${scrollProgress * 45}deg)` }}
      />
      {/* 3. Thin Luxury Rule Overlay */}
      <div className="absolute top-12 left-12 right-12 h-[1px] bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />
    </div>
  );
};
export default DynamicSpatialEnvironment;
