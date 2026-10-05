import React, { useEffect, useState } from 'react';

/**
 * Family D — Organic Digital Environment
 * Fluid emerald gradients, breathing organic blobs, liquid motion, soft geometry.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-emerald-950">
      {/* 1. Fluid Ambient Gradient Mesh */}
      <div 
        className="absolute inset-0 transition-all duration-700 ease-out"
        style={{
          background: `radial-gradient(circle at ${mousePos.x}% ${mousePos.y}%, rgba(16, 185, 129, 0.35) 0%, rgba(6, 182, 212, 0.2) 45%, rgba(2, 44, 34, 0.95) 100%)`
        }}
      />
      {/* 2. Morphing Organic Blob 1 */}
      <div 
        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-emerald-500/20 blur-[130px] animate-breathing-glow"
        style={{ transform: `translate3d(${(mousePos.x - 50) * 0.5}px, ${(mousePos.y - 50) * 0.5}px, 0)` }}
      />
      {/* 3. Morphing Organic Blob 2 */}
      <div 
        className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] rounded-full bg-teal-500/15 blur-[150px] animate-breathing-glow"
        style={{ animationDelay: '3s', transform: `translate3d(${(mousePos.x - 50) * -0.6}px, ${(mousePos.y - 50) * -0.6}px, 0)` }}
      />
    </div>
  );
};
export default DynamicSpatialEnvironment;
