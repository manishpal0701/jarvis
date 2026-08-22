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
                "lucide-react": "^0.344.0",
                "framer-motion": "^11.0.0",
                "clsx": "^2.1.0",
                "tailwind-merge": "^2.2.0",
                "next-themes": "^0.3.0",
                "react-hook-form": "^7.51.0"
            },
            "devDependencies": {
                "@types/react": "^18.3.3",
                "@types/react-dom": "^18.3.0",
                "@vitejs/plugin-react": "^4.3.1",
                "@tailwindcss/vite": "^4.0.0",
                "tailwindcss": "^4.0.0",
                "typescript": "^5.5.3",
                "vite": "^5.4.1"
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
            "import react from '@vitejs/plugin-react';\n"
            "import tailwindcss from '@tailwindcss/vite';\n\n"
            "// https://vitejs.dev/config/\n"
            "export default defineConfig({\n"
            "  plugins: [\n"
            "    react(),\n"
            "    tailwindcss(),\n"
            "  ],\n"
            "});\n"
        )

    @classmethod
    def generate_index_html(cls, biz_name: str = "Website", title: str = None) -> str:
        doc_title = title or f"{biz_name} — Professional React Website"
        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "  <head>\n"
            '    <meta charset="UTF-8" />\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            f"    <title>{doc_title}</title>\n"
            "  </head>\n"
            "  <body>\n"
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
    def generate_index_css(cls) -> str:
        return (
            '@import "tailwindcss";\n\n'
            '@theme {\n'
            '  --color-primary: #0284c7;\n'
            '  --color-secondary: #0f172a;\n'
            '  --color-accent: #38bdf8;\n'
            '}\n\n'
            'body {\n'
            '  margin: 0;\n'
            '  background-color: #090d16;\n'
            '  color: #f8fafc;\n'
            '  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;\n'
            '}\n'
        )
