"""
tools/coding/website_visual_environment.py
Centralized 3D Spatial Visual Environment Architecture for Website Builder v4.

Provides family-specific, GPU-accelerated 3D background environments:
- Family A (Cinematic Spatial): Cyber radial grid, rotating 3D orbit system, floating glass geometry.
- Family B (Swiss Editorial): Architectural grid canvas with thin rules and wireframe lines (No glowing ambient light).
- Family C (Experimental Brutalist): Noise grain mesh, volt green/magenta raw geometric containers, CRT scanlines.
- Family D (Organic Digital): Fluid breathing emerald orbs, morphing liquid SVG geometry.
- Family E (Editorial Luxury): Deep mahogany/ivory canvas with candlelit warm gold glow.
- Family F (Automotive Cinematic): Pitch black & electric red speed light streaks and light trails.
- Family G (Futuristic Interface): Monospace HUD telemetry data stream grid, holographic node mesh.
- Family H (Creative Agency): Expressive dark purple & coral color field morphing.
"""

from typing import Dict, Any, List

class WebsiteVisualEnvironment:
    """
    Architecturally centralized generator for 3D visual environment primitives.
    Guarantees family-specific, GPU-accelerated visual depth across generated websites.
    """

    @classmethod
    def get_environment_component_code(cls, category: str = "technology", theme: str = "dark_cyan", design_id: str = "cinematic_spatial") -> str:
        did_lower = (design_id or "").lower()
        cat_lower = (category or "").lower()

        # 0. GUSTAVO SPATIAL WIREFRAME LANDSCAPE (Reference-driven 3D Mesh)
        if "gustavo" in did_lower or "spatial" in did_lower or "portfolio" in cat_lower or "creative" in did_lower:
            return cls._get_gustavo_wireframe_landscape_environment()

        # 1. FAMILY B — SWISS EDITORIAL & ARCHITECTURE
        if "swiss" in did_lower or "architecture" in did_lower:
            return cls._get_swiss_editorial_environment()

        # 2. FAMILY C — EXPERIMENTAL BRUTALIST & NEO-RETRO
        elif "brutalist" in did_lower or "neo_retro" in did_lower:
            return cls._get_brutalist_environment()

        # 3. FAMILY D — ORGANIC DIGITAL
        elif "organic" in did_lower:
            return cls._get_organic_digital_environment()

        # 4. FAMILY E — EDITORIAL LUXURY & RESTAURANT & FASHION
        elif "luxury" in did_lower or "restaurant" in did_lower or "fashion" in did_lower or "dining" in cat_lower:
            return cls._get_editorial_luxury_environment()

        # 5. FAMILY F — AUTOMOTIVE CINEMATIC
        elif "automotive" in did_lower or "tesla" in cat_lower or "auto" in cat_lower:
            return cls._get_automotive_cinematic_environment()

        # 6. FAMILY G — FUTURISTIC INTERFACE & DATA & PRODUCT
        elif "hud" in did_lower or "futuristic" in did_lower or "data" in did_lower or "product" in did_lower:
            return cls._get_futuristic_interface_environment()

        # 7. FAMILY H — CREATIVE AGENCY
        elif "creative" in did_lower or "agency" in did_lower:
            return cls._get_creative_agency_environment()

        # 8. FAMILY A — CINEMATIC SPATIAL (Default)
        else:
            return cls._get_cinematic_spatial_environment()

    @classmethod
    def _get_swiss_editorial_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_brutalist_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

/**
 * Family C — Experimental Brutalist Environment
 * Noise grain mesh, volt green/magenta raw geometric shapes, hard edges, marquee drift.
 * NO glassmorphism, NO standard cyan glow.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({
        x: (e.clientX / window.innerWidth - 0.5) * 40,
        y: (e.clientY / window.innerHeight - 0.5) * 40
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-black text-white">
      {/* 1. High-Contrast Noise Grain Mesh */}
      <div className="absolute inset-0 bg-dots-pattern opacity-20" />
      {/* 2. Raw Offset Geometric Container */}
      <div 
        className="absolute top-1/4 left-10 w-96 h-96 border-4 border-[#ccff00]/30 transition-transform duration-100 ease-out"
        style={{ transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0) rotate(3deg)` }}
      />
      <div 
        className="absolute bottom-1/4 right-10 w-80 h-80 border-4 border-[#ff0055]/30 transition-transform duration-150 ease-out"
        style={{ transform: `translate3d(${mousePos.x * -1.2}px, ${mousePos.y * -1.2}px, 0) rotate(-5deg)` }}
      />
      {/* 3. Raw Diagonal Accent Line */}
      <div className="absolute top-0 right-1/3 w-[2px] h-full bg-[#ccff00]/20 transform -rotate-12" />
    </div>
  );
};
export default DynamicSpatialEnvironment;
"""

    @classmethod
    def _get_organic_digital_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_editorial_luxury_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_automotive_cinematic_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_futuristic_interface_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_creative_agency_environment(cls) -> str:
        return """import React, { useEffect, useState } from 'react';

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
"""

    @classmethod
    def _get_cinematic_spatial_environment(cls) -> str:
        return """import React, { useEffect, useRef, useState } from 'react';

/**
 * Family A — Cinematic Spatial Environment (Default)
 * Features active HTML5 particle network canvas, cursor node tracking, distance vector lines,
 * ambient radial lighting sweep, and floating 3D spatial geometry.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5, pxX: 0, pxY: 0 });
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const particleCount = Math.min(Math.floor(width / 25), 50);
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.7,
      vy: (Math.random() - 0.5) * 0.7,
      radius: Math.random() * 2 + 1,
      alpha: Math.random() * 0.5 + 0.3
    }));

    let mouseX = width / 2;
    let mouseY = height / 2;

    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;
      const pxX = (e.clientX - window.innerWidth / 2) * 0.05;
      const pxY = (e.clientY - window.innerHeight / 2) * 0.05;
      setMousePos({ x, y, pxX, pxY });
    };

    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      const progress = totalScroll > 0 ? window.scrollY / totalScroll : 0;
      setScrollProgress(progress);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(6, 182, 212, ${p.alpha})`;
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(6, 182, 212, ${0.22 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }

        const mdx = p.x - mouseX;
        const mdy = p.y - mouseY;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 160) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(mouseX, mouseY);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.35 * (1 - mdist / 160)})`;
          ctx.lineWidth = 1.1;
          ctx.stroke();
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-slate-950">
      {/* 1. Ambient Light Layer */}
      <div 
        className="absolute inset-0 transition-opacity duration-700"
        style={{
          background: `radial-gradient(circle at ${mousePos.x * 100}% ${mousePos.y * 100}%, rgba(6, 182, 212, 0.22) 0%, rgba(99, 102, 241, 0.15) 45%, rgba(3, 7, 18, 0.96) 100%)`,
          transform: `translate3d(${mousePos.pxX * -0.4}px, ${mousePos.pxY * -0.4}px, 0)`
        }}
      />
      {/* 2. Interactive Canvas Particle Network */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-65" />
      {/* 3. Floating 3D Spatial Geometry */}
      <div className="absolute inset-0 opacity-40">
        <div 
          className="absolute top-1/4 left-1/6 w-48 h-48 rounded-full border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-indigo-600/5 backdrop-blur-3xl animate-float-slow"
          style={{ transform: `translate3d(${mousePos.pxX * 1.5}px, ${mousePos.pxY * 1.5 - scrollProgress * 60}px, 0) rotate(${scrollProgress * 90}deg)` }}
        />
        <div 
          className="absolute bottom-1/3 right-1/6 w-64 h-64 rounded-full border border-indigo-500/20 bg-gradient-to-tr from-indigo-500/10 to-purple-600/5 backdrop-blur-3xl animate-float-slow"
          style={{ animationDelay: '2s', transform: `translate3d(${mousePos.pxX * -1.2}px, ${mousePos.pxY * -1.2 + scrollProgress * 40}px, 0) rotate(${scrollProgress * -60}deg)` }}
        />
      </div>
    </div>
  );
};
export default DynamicSpatialEnvironment;
"""

    @classmethod
    def _get_gustavo_wireframe_landscape_environment(cls) -> str:
        return """import React, { useEffect, useRef, useState } from 'react';

/**
 * Family Gustavo — Spatial Interactive Wireframe Terrain Mesh (Gustavo Batista Reference)
 * Renders a full-viewport 3D wireframe mesh terrain in real-time HTML5 Canvas 2D/3D projection,
 * featuring interactive mouse perspective tilting and scroll-driven 3D camera z-translation.
 */
export const DynamicSpatialEnvironment: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    let mouseX = width / 2;
    let mouseY = height / 2;
    let targetMouseX = width / 2;
    let targetMouseY = height / 2;

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = e.clientX;
      targetMouseY = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    let scrollY = window.scrollY;
    const handleScroll = () => {
      scrollY = window.scrollY;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    let frame = 0;
    const gridCols = 36;
    const gridRows = 30;
    const spacing = 42;

    const render = () => {
      frame += 0.015;
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      ctx.fillStyle = '#030712';
      ctx.fillRect(0, 0, width, height);

      // Radial ambient lighting
      const grad = ctx.createRadialGradient(mouseX, mouseY, 10, mouseX, mouseY, width * 0.75);
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.16)');
      grad.addColorStop(0.5, 'rgba(16, 185, 129, 0.07)');
      grad.addColorStop(1, 'rgba(3, 7, 18, 0.98)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // 3D Terrain Wireframe Mesh Projection
      const tiltX = (mouseY - height / 2) * 0.00045;
      const tiltY = (mouseX - width / 2) * 0.00045;
      const cameraZ = 280 + (scrollY * 0.35);

      const projectedPoints: { x: number; y: number; z: number }[][] = [];

      for (let r = 0; r < gridRows; r++) {
        const rowPoints: { x: number; y: number; z: number }[] = [];
        for (let c = 0; c < gridCols; c++) {
          const worldX = (c - gridCols / 2) * spacing;
          const worldY = (r - gridRows / 2) * spacing;

          // Procedural Terrain Height Formula
          const distFromCenter = Math.sqrt(worldX * worldX + worldY * worldY);
          const terrainZ = Math.sin(c * 0.35 + frame) * Math.cos(r * 0.35 + frame) * 38 +
                           Math.sin(distFromCenter * 0.02 - frame) * 22;

          // 3D Rotation Matrix
          const cosX = Math.cos(tiltX);
          const sinX = Math.sin(tiltX);
          const cosY = Math.cos(tiltY);
          const sinY = Math.sin(tiltY);

          let ry = worldY * cosX - terrainZ * sinX;
          let rz = worldY * sinX + terrainZ * cosX + cameraZ;

          let rx = worldX * cosY + rz * sinY;
          let finalZ = -worldX * sinY + rz * cosY;

          // Perspective Projection
          const fov = 450;
          const scale = fov / (fov + finalZ);
          const projX = width / 2 + rx * scale;
          const projY = height / 2 + ry * scale + 60;

          rowPoints.push({ x: projX, y: projY, z: finalZ });
        }
        projectedPoints.push(rowPoints);
      }

      // Draw Wireframe Mesh Lines
      ctx.lineWidth = 0.7;

      for (let r = 0; r < gridRows; r++) {
        for (let c = 0; c < gridCols; c++) {
          const p = projectedPoints[r][c];

          // Horizontal wire line
          if (c < gridCols - 1) {
            const pRight = projectedPoints[r][c + 1];
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(pRight.x, pRight.y);
            const alpha = Math.max(0, 0.38 - (p.z / 1100));
            ctx.strokeStyle = `rgba(200, 220, 245, ${alpha})`;
            ctx.stroke();
          }

          // Vertical wire line
          if (r < gridRows - 1) {
            const pDown = projectedPoints[r + 1][c];
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(pDown.x, pDown.y);
            const alpha = Math.max(0, 0.38 - (p.z / 1100));
            ctx.strokeStyle = `rgba(200, 220, 245, ${alpha})`;
            ctx.stroke();
          }
        }
      }

      // Draw interactive particle nodes
      for (let r = 0; r < gridRows; r += 2) {
        for (let c = 0; c < gridCols; c += 2) {
          const p = projectedPoints[r][c];
          if (p.z > 0 && p.z < 1000) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1.2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(56, 189, 248, ${0.55 - p.z / 1800})`;
            ctx.fill();
          }
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#030712]">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
};
export default DynamicSpatialEnvironment;
"""

    @classmethod
    def get_primitives_manifest(cls) -> List[str]:
        return [
            "DynamicSpatialBackground", "AnimatedMeshField", "ParticleField",
            "SpatialGrid", "OrbitSystem", "FloatingGeometry", "EnergyField",
            "AmbientLightLayer", "DynamicGlow", "DepthAtmosphere",
            "ParallaxEnvironment", "CursorLight", "ScrollEnvironment", "NoiseLayer"
        ]
