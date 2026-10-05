import json
import re

class WebsiteProjectTemplates:
    """
    Deterministic template generator for React + TypeScript + Tailwind CSS v4 + Vite projects.
    Infrastructure files (package.json, tsconfig.json, vite.config.ts, index.html, src/main.tsx)
    are generated 100% deterministically in Python, eliminating LLM errors and retries.
    """

    @classmethod
    def generate_package_json(cls, biz_name: str = "React App", project_name: str = "react_website") -> str:
        clean_name = re.sub(r'[^a-z0-9_-]', '_', project_name.lower().strip()) or "react_website"
        pkg_data = {
            "name": clean_name,
            "private": True,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "lucide-react": "^0.344.0"
            },
            "devDependencies": {
                "@types/react": "^18.3.3",
                "@types/react-dom": "^18.3.0",
                "@vitejs/plugin-react": "^4.2.1",
                "typescript": "^5.2.2",
                "vite": "^5.2.0"
            }
        }
        return json.dumps(pkg_data, indent=2)

    @classmethod
    def generate_tsconfig(cls) -> str:
        tsconfig_data = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": False,
                "noUnusedParameters": False,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"]
        }
        return json.dumps(tsconfig_data, indent=2)

    @classmethod
    def generate_vite_config(cls) -> str:
        return (
            "import { defineConfig } from 'vite';\n"
            "import react from '@vitejs/plugin-react';\n\n"
            "// https://vitejs.dev/config/\n"
            "export default defineConfig({\n"
            "  plugins: [react()],\n"
            "});\n"
        )

    @classmethod
    def generate_index_html(cls, biz_name: str = "Website", title: str = None) -> str:
        doc_title = title or f"{biz_name} — Professional React Website"
        return (
            "<!DOCTYPE html>\n"
            '<html lang="en" class="dark">\n'
            "  <head>\n"
            '    <meta charset="UTF-8" />\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            f"    <title>{doc_title}</title>\n"
            '    <script src="https://cdn.tailwindcss.com"></script>\n'
            '    <link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" media="print" onload="this.media=\'all\'">\n'
            '    <noscript>\n'
            '      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">\n'
            '    </noscript>\n'
            "  </head>\n"
            '  <body class="bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">\n'
            '    <div id="root"></div>\n'
            '    <script type="module" src="/src/main.tsx"></script>\n'
            "  </body>\n"
            "</html>\n"
        )

    @classmethod
    def generate_main_tsx(cls) -> str:
        return (
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            "import App from './App.tsx';\n"
            "import './index.css';\n\n"
            "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
            "  <React.StrictMode>\n"
            "    <App />\n"
            "  </React.StrictMode>,\n"
            ");\n"
        )

    @classmethod
    def generate_index_css(cls, design_id: str = "cinematic_spatial") -> str:
        did_lower = (design_id or "").lower()
        bg_hex = "#fafafa" if "swiss" in did_lower or "fashion" in did_lower else "#0c0a09" if "editorial" in did_lower or "restaurant" in did_lower else "#000000" if "brutalist" in did_lower else "#030712"
        text_hex = "#0a0a0a" if "swiss" in did_lower or "fashion" in did_lower else "#ffffff"

        return (
            "@tailwind base;\n"
            "@tailwind components;\n"
            "@tailwind utilities;\n\n"
            ":root {\n"
            "  --mouse-x: 0.5;\n"
            "  --mouse-y: 0.5;\n"
            "  --scroll-progress: 0;\n"
            "  --section-active: 0;\n"
            "}\n\n"
            "html {\n"
            "  scroll-behavior: smooth;\n"
            "}\n\n"
            "body {\n"
            "  margin: 0;\n"
            f"  background-color: {bg_hex};\n"
            f"  color: {text_hex};\n"
            '  font-family: "Space Grotesk", "Inter", system-ui, -apple-system, sans-serif;\n'
            "  overflow-x: hidden;\n"
            "}\n\n"
            "/* True 3D & Spatial Perspective Utilities */\n"
            ".perspective-1000 {\n"
            "  perspective: 1000px;\n"
            "}\n"
            ".perspective-1200 {\n"
            "  perspective: 1200px;\n"
            "}\n"
            ".perspective-2000 {\n"
            "  perspective: 2000px;\n"
            "}\n"
            ".preserve-3d {\n"
            "  transform-style: preserve-3d;\n"
            "}\n"
            ".backface-hidden {\n"
            "  backface-visibility: hidden;\n"
            "}\n\n"
            "/* 7 Spatial Depth Layer System (DEPTH 0 to DEPTH 6) */\n"
            ".depth-0, .depth-layer-bg {\n"
            "  transform: translateZ(-250px) scale(1.25);\n"
            "  z-index: 0;\n"
            "}\n"
            ".depth-1, .depth-layer-atmosphere {\n"
            "  transform: translateZ(-150px) scale(1.15);\n"
            "  z-index: 1;\n"
            "}\n"
            ".depth-2, .depth-layer-geometry {\n"
            "  transform: translateZ(-80px) scale(1.08);\n"
            "  z-index: 2;\n"
            "}\n"
            ".depth-3, .depth-layer-object {\n"
            "  transform: translateZ(0px);\n"
            "  z-index: 3;\n"
            "}\n"
            ".depth-4, .depth-layer-ui {\n"
            "  transform: translateZ(40px);\n"
            "  z-index: 4;\n"
            "}\n"
            ".depth-5, .depth-layer-fg {\n"
            "  transform: translateZ(90px);\n"
            "  z-index: 5;\n"
            "}\n"
            ".depth-6, .depth-layer-cta {\n"
            "  transform: translateZ(140px);\n"
            "  z-index: 6;\n"
            "}\n\n"
            "/* Interactive Parallax & Tilt */\n"
            ".card-3d-tilt {\n"
            "  transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.4s ease, border-color 0.4s ease;\n"
            "  transform-style: preserve-3d;\n"
            "}\n"
            ".card-3d-tilt:hover {\n"
            "  transform: translateY(-8px) rotateX(6deg) rotateY(-6deg) translateZ(20px);\n"
            "  box-shadow: 0 25px 50px -12px rgba(6, 182, 212, 0.25);\n"
            "}\n\n"
            "/* Glassmorphism & Atmospheric Lighting */\n"
            ".glass-panel {\n"
            "  background: rgba(15, 23, 42, 0.7);\n"
            "  backdrop-filter: blur(20px);\n"
            "  -webkit-backdrop-filter: blur(20px);\n"
            "  border: 1px solid rgba(255, 255, 255, 0.12);\n"
            "}\n"
            ".glass-card {\n"
            "  background: rgba(30, 41, 59, 0.55);\n"
            "  backdrop-filter: blur(14px);\n"
            "  border: 1px solid rgba(255, 255, 255, 0.08);\n"
            "}\n"
            ".spatial-glass-panel {\n"
            "  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.4) 100%);\n"
            "  backdrop-filter: blur(24px);\n"
            "  -webkit-backdrop-filter: blur(24px);\n"
            "  border: 1px solid rgba(56, 189, 248, 0.2);\n"
            "  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.2);\n"
            "}\n"
            ".glow-cyan {\n"
            "  box-shadow: 0 0 35px rgba(6, 182, 212, 0.4);\n"
            "}\n"
            ".glow-cyan-spatial {\n"
            "  filter: drop-shadow(0 0 20px rgba(6, 182, 212, 0.5));\n"
            "}\n"
            ".glow-amber-spatial {\n"
            "  filter: drop-shadow(0 0 20px rgba(245, 158, 11, 0.5));\n"
            "}\n\n"
            "/* Spatial Grids & Mesh Backgrounds */\n"
            ".bg-spatial-grid {\n"
            "  background-size: 50px 50px;\n"
            "  background-image: \n"
            "    linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px),\n"
            "    linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px);\n"
            "}\n"
            ".bg-dots-pattern {\n"
            "  background-image: radial-gradient(rgba(56, 189, 248, 0.15) 1px, transparent 1px);\n"
            "  background-size: 24px 24px;\n"
            "}\n"
            ".bg-cyber-radial {\n"
            "  background: radial-gradient(circle at 50% 30%, rgba(6, 182, 212, 0.15) 0%, rgba(15, 23, 42, 0.8) 50%, rgba(3, 7, 18, 1) 100%);\n"
            "}\n\n"
            "/* Keyframe Animations */\n"
            "@keyframes floatSlow {\n"
            "  0%, 100% { transform: translateY(0px) rotate(0deg); }\n"
            "  50% { transform: translateY(-16px) rotate(2deg); }\n"
            "}\n"
            ".animate-float-slow {\n"
            "  animation: floatSlow 7s ease-in-out infinite;\n"
            "}\n"
            "@keyframes rotateSlow {\n"
            "  from { transform: rotate(0deg); }\n"
            "  to { transform: rotate(360deg); }\n"
            "}\n"
            ".animate-rotate-slow {\n"
            "  animation: rotateSlow 25s linear infinite;\n"
            "}\n"
            "@keyframes orbit {\n"
            "  from { transform: rotate(0deg) translateX(120px) rotate(0deg); }\n"
            "  to { transform: rotate(360deg) translateX(120px) rotate(-360deg); }\n"
            "}\n"
            ".animate-orbit {\n"
            "  animation: orbit 18s linear infinite;\n"
            "}\n"
            "@keyframes breathingGlow {\n"
            "  0%, 100% { opacity: 0.35; transform: scale(1); filter: blur(40px); }\n"
            "  50% { opacity: 0.75; transform: scale(1.15); filter: blur(55px); }\n"
            "}\n"
            ".animate-breathing-glow {\n"
            "  animation: breathingGlow 5s ease-in-out infinite;\n"
            "}\n"
            "@keyframes pulseGlow {\n"
            "  0%, 100% { opacity: 0.4; transform: scale(1); }\n"
            "  50% { opacity: 0.85; transform: scale(1.06); }\n"
            "}\n"
            ".animate-pulse-glow {\n"
            "  animation: pulseGlow 4s ease-in-out infinite;\n"
            "}\n"
            "@keyframes marquee {\n"
            "  0% { transform: translateX(0%); }\n"
            "  100% { transform: translateX(-50%); }\n"
            "}\n"
            ".animate-marquee {\n"
            "  display: flex;\n"
            "  width: 200%;\n"
            "  animation: marquee 25s linear infinite;\n"
            "}\n"
            ".animate-marquee:hover {\n"
            "  animation-play-state: paused;\n"
            "}\n"
        )

