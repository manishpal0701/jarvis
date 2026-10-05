import React, { useEffect, useRef, useState } from 'react';

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
