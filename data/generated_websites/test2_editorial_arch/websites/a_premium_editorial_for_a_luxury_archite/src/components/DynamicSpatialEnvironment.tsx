import React, { useEffect, useState } from 'react';

/**
 * Family H — Creative Agency Environment
 * Expressive dark purple & coral accent fields with dynamic morphing shapes.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#1a0933]">
      {/* 1. Expressive Coral & Purple Gradient Field */}
      <div 
        className="absolute inset-0 transition-all duration-500 ease-out"
        style={{
          background: `radial-gradient(circle at ${mousePos.x * 100}% ${mousePos.y * 100}%, rgba(255, 107, 107, 0.3) 0%, rgba(78, 205, 196, 0.2) 50%, rgba(26, 9, 51, 0.95) 100%)`
        }}
      />
      {/* 2. Abstract Morphing Shape */}
      <div className="absolute top-1/4 right-1/4 w-[450px] h-[450px] bg-gradient-to-tr from-coral-500/20 to-purple-600/30 rounded-[40%_60%_70%_30%] blur-[90px] animate-float-slow" />
    </div>
  );
};
export default DynamicSpatialEnvironment;
