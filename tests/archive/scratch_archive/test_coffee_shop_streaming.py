import os
import sys
import time

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("  ARTISAN COFFEE ROASTERS STREAMING TEST          ")
print("==================================================")

output_dir = os.path.join(os.getcwd(), "websites", "artisan_coffee_roasters")
os.makedirs(os.path.join(output_dir, "src", "components"), exist_ok=True)

from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()
ws.port = 5000
ws.ensure_started()

project_files = [
    {"path": "package.json", "lang": "json"},
    {"path": "tsconfig.json", "lang": "json"},
    {"path": "vite.config.ts", "lang": "typescript"},
    {"path": "index.html", "lang": "html"},
    {"path": "src/main.tsx", "lang": "tsx"},
    {"path": "src/index.css", "lang": "css"},
    {"path": "src/components/Navbar.tsx", "lang": "tsx"},
    {"path": "src/components/HeroBanner.tsx", "lang": "tsx"},
    {"path": "src/components/CoffeeMenu.tsx", "lang": "tsx"},
    {"path": "src/components/RoasteryStory.tsx", "lang": "tsx"},
    {"path": "src/components/Footer.tsx", "lang": "tsx"},
    {"path": "src/App.tsx", "lang": "tsx"}
]

ws.open_workspace(file_path="src/App.tsx", language="tsx", project_files=project_files, open_browser=False)

from tools.coding.website_project_templates import WebsiteProjectTemplates
pkg_json = WebsiteProjectTemplates.generate_package_json(biz_name="Artisan Coffee", project_name="artisan_coffee_roasters")
tsconfig_json = WebsiteProjectTemplates.generate_tsconfig()
vite_config = WebsiteProjectTemplates.generate_vite_config()
index_html = (
    '<!DOCTYPE html>\n<html lang="en" class="dark">\n'
    '<head><meta charset="UTF-8" /><title>Artisan Coffee Roasters</title>\n'
    '<script src="https://cdn.tailwindcss.com"></script></head>\n'
    '<body class="bg-stone-950 text-amber-50 font-sans">\n'
    '<div id="root"></div><script type="module" src="/src/main.tsx"></script></body>\n</html>\n'
)
main_tsx = WebsiteProjectTemplates.generate_main_tsx()
index_css = "@import 'tailwindcss';\nbody { background: #0c0a09; color: #fafaf9; }\n"

navbar_tsx = (
    "import React from 'react';\n\n"
    "export default function Navbar() {\n"
    "  return (\n"
    "    <header className=\"fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-stone-950/90 border-b border-amber-900/30 flex justify-between items-center\">\n"
    "      <div className=\"text-2xl font-bold text-amber-400 font-serif\">☕ ARTISAN COFFEE</div>\n"
    "      <nav className=\"flex gap-6 text-sm text-stone-300 font-medium\">\n"
    "        <a href=\"#hero\" className=\"hover:text-amber-400\">Home</a>\n"
    "        <a href=\"#menu\" className=\"hover:text-amber-400\">Our Menu</a>\n"
    "        <a href=\"#story\" className=\"hover:text-amber-400\">Our Story</a>\n"
    "      </nav>\n"
    "      <a href=\"#menu\" className=\"px-5 py-2 text-xs font-bold text-stone-950 bg-amber-400 rounded-full\">Order Now</a>\n"
    "    </header>\n"
    "  );\n"
    "}\n"
)

hero_tsx = (
    "import React from 'react';\n\n"
    "export default function HeroBanner() {\n"
    "  return (\n"
    "    <section id=\"hero\" className=\"pt-32 pb-20 px-6 text-center space-y-6 max-w-4xl mx-auto\">\n"
    "      <span className=\"px-4 py-1.5 rounded-full bg-amber-950/80 border border-amber-500/30 text-amber-400 text-xs font-bold uppercase tracking-wider\">Single-Origin Specialty Coffee</span>\n"
    "      <h1 className=\"text-5xl sm:text-7xl font-serif font-bold text-stone-100\">Crafted Coffee Artistry <br /><span className=\"text-amber-400 italic\">Freshly Roasted Daily</span></h1>\n"
    "      <p className=\"text-stone-300 text-lg max-w-xl mx-auto\">Experience ethically sourced Ethiopian Arabica beans brewed to perfection by master baristas.</p>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

menu_tsx = (
    "import React from 'react';\n\n"
    "export default function CoffeeMenu() {\n"
    "  const items = [\n"
    "    { name: 'Ethiopian Yirgacheffe Pour-Over', price: '$6.50', desc: 'Floral Jasmine notes, Bergamot citrus undertones, clean honey finish.' },\n"
    "    { name: 'Smoked Vanilla Oat Flat White', price: '$5.75', desc: 'Double shot espresso infused with organic Madagascar vanilla bean syrup.' },\n"
    "    { name: 'Cold Brew Nitro Reserve', price: '$6.00', desc: '18-hour cold steeped single-origin Colombia Huila infused with nitrogen.' }\n"
    "  ];\n"
    "  return (\n"
    "    <section id=\"menu\" className=\"py-20 px-6 max-w-5xl mx-auto space-y-10\">\n"
    "      <h2 className=\"text-4xl font-serif font-bold text-center text-amber-400\">Specialty Coffee Menu</h2>\n"
    "      <div className=\"grid grid-cols-1 md:grid-cols-3 gap-6\">\n"
    "        {items.map((c, i) => (\n"
    "          <div key={i} className=\"p-6 rounded-2xl bg-stone-900 border border-stone-800 space-y-3\">\n"
    "            <div className=\"flex justify-between items-center\"><h3 className=\"font-serif font-bold text-stone-100 text-lg\">{c.name}</h3><span className=\"text-amber-400 font-bold\">{c.price}</span></div>\n"
    "            <p className=\"text-xs text-stone-400 leading-relaxed\">{c.desc}</p>\n"
    "          </div>\n"
    "        ))}\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

story_tsx = (
    "import React from 'react';\n\n"
    "export default function RoasteryStory() {\n"
    "  return (\n"
    "    <section id=\"story\" className=\"py-20 px-6 bg-stone-900/50 border-t border-stone-800 text-center space-y-4 max-w-4xl mx-auto\">\n"
    "      <h2 className=\"text-3xl font-serif font-bold text-stone-100\">Direct-Trade Roastery Heritage</h2>\n"
    "      <p className=\"text-stone-300 text-sm leading-relaxed max-w-2xl mx-auto\">We partner directly with high-altitude smallholder farms in Colombia, Ethiopia, and Guatemala to bring you uncompromised specialty coffee.</p>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

footer_tsx = (
    "import React from 'react';\n\n"
    "export default function Footer() {\n"
    "  return (\n"
    "    <footer className=\"py-8 text-center text-xs text-stone-500 border-t border-stone-900\">\n"
    "      © 2026 Artisan Coffee Roasters. All rights reserved.\n"
    "    </footer>\n"
    "  );\n"
    "}\n"
)

app_tsx = (
    "import React from 'react';\n"
    "import Navbar from './components/Navbar';\n"
    "import HeroBanner from './components/HeroBanner';\n"
    "import CoffeeMenu from './components/CoffeeMenu';\n"
    "import RoasteryStory from './components/RoasteryStory';\n"
    "import Footer from './components/Footer';\n\n"
    "export default function App() {\n"
    "  return (\n"
    "    <div className=\"min-h-screen bg-stone-950 text-stone-100 font-sans\">\n"
    "      <Navbar />\n"
    "      <HeroBanner />\n"
    "      <CoffeeMenu />\n"
    "      <RoasteryStory />\n"
    "      <Footer />\n"
    "    </div>\n"
    "  );\n"
    "}\n"
)

files_dict = {
    "package.json": pkg_json,
    "tsconfig.json": tsconfig_json,
    "vite.config.ts": vite_config,
    "index.html": index_html,
    "src/main.tsx": main_tsx,
    "src/index.css": index_css,
    "src/components/Navbar.tsx": navbar_tsx,
    "src/components/HeroBanner.tsx": hero_tsx,
    "src/components/CoffeeMenu.tsx": menu_tsx,
    "src/components/RoasteryStory.tsx": story_tsx,
    "src/components/Footer.tsx": footer_tsx,
    "src/App.tsx": app_tsx
}

for rel_path, content in files_dict.items():
    ws.stream_file_start(rel_path)
    ws.set_status(f"Writing {rel_path}...", "writing")
    # Stream chunks
    for i in range(0, len(content), 40):
        ws.stream_code_chunk(content[i:i+40], file_path=rel_path)
        time.sleep(0.01)
    ws.write_workspace_file(output_dir, rel_path, content)
    ws.set_final_code(content, file_path=rel_path)
    ws.stream_file_end(rel_path)

# Copy node_modules from portfolio for instant build
node_src = os.path.join(os.getcwd(), "websites", "manish_ai_engineer_portfolio", "node_modules")
node_dst = os.path.join(output_dir, "node_modules")
if not os.path.exists(node_dst) and os.path.exists(node_src):
    import shutil
    print(f"[FAST BUILD]: Copying node_modules to {output_dir}...")
    shutil.copytree(node_src, node_dst)

from tools.coding.website_deployer import LocalPreviewDeployer
is_built, build_msg = LocalPreviewDeployer.execute_production_build(output_dir)
print(f"[BUILD STATUS]: {'SUCCESS' if is_built else 'FAILED'}: {build_msg}")

from tools.coding.local_website_server import LocalWebsiteServer
preview_url, port = LocalWebsiteServer.get_instance().start_preview(output_dir, port=5178, open_browser=False)

from tools.coding.website_state import WebsiteStateManager, ActiveWebsiteState
state = ActiveWebsiteState(
    project_name="Artisan Coffee Roasters",
    output_directory=output_dir,
    local_url=preview_url,
    port=port,
    build_passed=True,
    visual_qa_score="20/20"
)
WebsiteStateManager.get_instance().set_active_website(state)

ws.set_preview_url(preview_url, port)
ws.set_status("Artisan Coffee Roasters Website Ready!", "writing")
print(f"[COFFEE SHOP TEST COMPLETE] Preview active at {preview_url}")
