import os
import sys
import time

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("==================================================")
print("  BELLA TAVOLA ITALIAN RESTAURANT E2E GENERATION  ")
print("==================================================")

t_start = time.perf_counter()

prompt = ("Jarvis, ek premium modern Italian restaurant ki website bana do. "
          "Restaurant ka naam Bella Tavola hai. Website classy, luxurious aur appetizing honi chahiye. "
          "Menu, signature dishes, restaurant story, gallery, location, opening hours aur table reservation CTA hona chahiye.")

output_dir = os.path.join(os.getcwd(), "websites", "bella_tavola_ristorante_italiano")
os.makedirs(os.path.join(output_dir, "src", "components"), exist_ok=True)

# 1. Research & Content Strategy
from tools.coding.website_researcher import WebsiteResearcher
from tools.coding.website_content_strategist import WebsiteContentStrategist
from tools.coding.website_design_system import WebsiteDesignSystemGenerator

res_spec = WebsiteResearcher.conduct_research(prompt, category="restaurant")
content_spec = WebsiteContentStrategist.generate_content_strategy(res_spec, prompt)
ds_spec = WebsiteDesignSystemGenerator.generate_design_system(res_spec, prompt)

print(f"[STAGE 1 - RESEARCH] Category: {res_spec.website_type}")
print(f"[STAGE 2 - CONTENT] Brand: {content_spec.person_or_brand_name}, Tagline: {content_spec.tagline}")
print(f"[STAGE 3 - DESIGN SYSTEM] Theme: {ds_spec.theme_name}, Font: {ds_spec.font_heading}, Primary: {ds_spec.primary_color}")

# 2. Component Files Dict
from tools.coding.website_project_templates import WebsiteProjectTemplates

pkg_json = WebsiteProjectTemplates.generate_package_json(biz_name="Bella Tavola", project_name="bella_tavola_ristorante_italiano")
tsconfig_json = WebsiteProjectTemplates.generate_tsconfig()
vite_config = WebsiteProjectTemplates.generate_vite_config()
index_html = (
    '<!DOCTYPE html>\n'
    '<html lang="en" class="dark">\n'
    '  <head>\n'
    '    <meta charset="UTF-8" />\n'
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
    '    <title>Bella Tavola — Ristorante Italiano Classico</title>\n'
    '    <script src="https://cdn.tailwindcss.com"></script>\n'
    '    <link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n'
    '  </head>\n'
    '  <body class="bg-stone-950 text-stone-100 font-sans antialiased selection:bg-amber-500 selection:text-stone-950">\n'
    '    <div id="root"></div>\n'
    '    <script type="module" src="/src/main.tsx"></script>\n'
    '  </body>\n'
    '</html>\n'
)
main_tsx = WebsiteProjectTemplates.generate_main_tsx()

index_css = (
    '@import "tailwindcss";\n\n'
    ':root {\n'
    '  --color-primary: #f59e0b;\n'
    '  --color-surface: #1c1917;\n'
    '}\n\n'
    'body {\n'
    '  margin: 0;\n'
    '  background-color: #0c0a09;\n'
    '  color: #fafaf9;\n'
    '  font-family: "Inter", system-ui, sans-serif;\n'
    '}\n\n'
    '.font-serif {\n'
    '  font-family: "Playfair Display", Georgia, serif;\n'
    '}\n\n'
    '.culinary-panel {\n'
    '  background: rgba(28, 25, 23, 0.85);\n'
    '  backdrop-filter: blur(16px);\n'
    '  border: 1px solid rgba(217, 119, 6, 0.3);\n'
    '}\n\n'
    '.culinary-card {\n'
    '  background: rgba(28, 25, 23, 0.7);\n'
    '  border: 1px solid rgba(68, 64, 60, 0.8);\n'
    '  transition: all 0.3s ease;\n'
    '}\n\n'
    '.culinary-card:hover {\n'
    '  background: rgba(28, 25, 23, 0.95);\n'
    '  border-color: rgba(245, 158, 11, 0.6);\n'
    '  box-shadow: 0 12px 35px -10px rgba(245, 158, 11, 0.25);\n'
    '  transform: translateY(-4px);\n'
    '}\n'
)

navbar_tsx = (
    "import React, { useState } from 'react';\n\n"
    "export default function Navbar() {\n"
    "  const [mobileMenu, setMobileMenu] = useState(false);\n"
    "  return (\n"
    "    <header className=\"fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-stone-950/85 backdrop-blur-md border-b border-amber-900/30\">\n"
    "      <div className=\"max-w-7xl mx-auto flex items-center justify-between\">\n"
    "        <a href=\"#\" className=\"flex items-center gap-2 text-2xl font-serif font-bold text-amber-400 tracking-wider\">\n"
    "          <span className=\"text-amber-500\">⚜</span> BELLA TAVOLA\n"
    "        </a>\n"
    "        <nav className=\"hidden md:flex items-center gap-8 text-sm font-medium text-stone-300\">\n"
    "          <a href=\"#hero\" className=\"hover:text-amber-400 transition-colors\">Home</a>\n"
    "          <a href=\"#dishes\" className=\"hover:text-amber-400 transition-colors\">Signature Dishes</a>\n"
    "          <a href=\"#menu\" className=\"hover:text-amber-400 transition-colors\">Full Menu</a>\n"
    "          <a href=\"#story\" className=\"hover:text-amber-400 transition-colors\">Our Story</a>\n"
    "          <a href=\"#hours\" className=\"hover:text-amber-400 transition-colors\">Hours & Location</a>\n"
    "        </nav>\n"
    "        <div className=\"flex items-center gap-4\">\n"
    "          <a href=\"#reservation\" className=\"px-6 py-2.5 text-xs font-bold uppercase tracking-widest text-stone-950 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 rounded-full shadow-md shadow-amber-500/20 hover:shadow-amber-500/40 hover:scale-105 transition-all\">\n"
    "            Reserve Table\n"
    "          </a>\n"
    "          <button onClick={() => setMobileMenu(!mobileMenu)} className=\"md:hidden p-2 text-stone-300 hover:text-amber-400\">\n"
    "            ☰\n"
    "          </button>\n"
    "        </div>\n"
    "      </div>\n"
    "      {mobileMenu && (\n"
    "        <div className=\"md:hidden mt-4 pt-4 border-t border-stone-800 flex flex-col gap-4 text-sm text-stone-200\">\n"
    "          <a href=\"#dishes\" onClick={() => setMobileMenu(false)}>Signature Dishes</a>\n"
    "          <a href=\"#menu\" onClick={() => setMobileMenu(false)}>Menu</a>\n"
    "          <a href=\"#story\" onClick={() => setMobileMenu(false)}>Our Story</a>\n"
    "          <a href=\"#reservation\" onClick={() => setMobileMenu(false)}>Reservations</a>\n"
    "        </div>\n"
    "      )}\n"
    "    </header>\n"
    "  );\n"
    "}\n"
)

hero_tsx = (
    "import React from 'react';\n\n"
    "export default function HeroBanner() {\n"
    "  return (\n"
    "    <section id=\"hero\" className=\"relative min-h-screen pt-32 pb-20 px-6 flex items-center justify-center overflow-hidden\">\n"
    "      <div className=\"absolute inset-0 z-0\">\n"
    "        <img src=\"https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=1920&q=80\" alt=\"Gourmet Italian Pasta Hero\" className=\"w-full h-full object-cover opacity-35 filter brightness-75\" />\n"
    "        <div className=\"absolute inset-0 bg-gradient-to-b from-stone-950/80 via-stone-950/60 to-stone-950\"></div>\n"
    "      </div>\n"
    "      <div className=\"relative z-10 max-w-4xl mx-auto text-center space-y-8\">\n"
    "        <div className=\"inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-950/70 border border-amber-500/40 text-amber-300 text-xs font-medium uppercase tracking-widest\">\n"
    "          <span>✦</span> Authentic Tuscan Gastronomy <span>✦</span>\n"
    "        </div>\n"
    "        <h1 className=\"text-4xl sm:text-6xl lg:text-7xl font-serif font-bold text-stone-100 tracking-tight leading-tight\">\n"
    "          Authentic Italian Culinary Artistry <br />\n"
    "          <span className=\"bg-gradient-to-r from-amber-200 via-amber-400 to-amber-600 bg-clip-text text-transparent italic\">\n"
    "            in Modern Elegance\n"
    "          </span>\n"
    "        </h1>\n"
    "        <p className=\"text-lg sm:text-xl text-stone-300 max-w-2xl mx-auto font-light leading-relaxed\">\n"
    "          Immerse yourself in handcrafted Tuscan pasta, wood-fired stone oven pizzas, and vintage Chianti Classico wines prepared by Executive Chef Marco Rossi.\n"
    "        </p>\n"
    "        <div className=\"flex flex-wrap items-center justify-center gap-5 pt-4\">\n"
    "          <a href=\"#reservation\" className=\"px-8 py-4 text-sm font-bold uppercase tracking-wider text-stone-950 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 rounded-full shadow-xl shadow-amber-500/25 hover:shadow-amber-500/45 hover:scale-105 transition-all\">\n"
    "            Reserve Your Table\n"
    "          </a>\n"
    "          <a href=\"#dishes\" className=\"px-8 py-4 text-sm font-semibold uppercase tracking-wider text-amber-200 bg-stone-900/80 hover:bg-stone-800 border border-amber-500/40 rounded-full transition-all\">\n"
    "            Explore Signature Menu &rarr;\n"
    "          </a>\n"
    "        </div>\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

dishes_tsx = (
    "import React from 'react';\n\n"
    "export default function SignatureDishes() {\n"
    "  const dishes = [\n"
    "    {\n"
    "      name: 'Tagliolini al Tartufo Nero',\n"
    "      category: 'Primi Piatti',\n"
    "      price: '$34',\n"
    "      description: 'Hand-rolled egg tagliolini tossed in cultured Parmigiano Reggiano butter and shaved Black Norcia Truffles.',\n"
    "      image: 'https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=800&q=80'\n"
    "    },\n"
    "    {\n"
    "      name: 'Pizza Margherita Verace',\n"
    "      category: 'Wood-Fired Pizza',\n"
    "      price: '$26',\n"
    "      description: 'San Marzano DOP tomatoes, Mozzarella di Bufala Campana, fresh basil, and extra virgin Tuscan olive oil.',\n"
    "      image: 'https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=800&q=80'\n"
    "    },\n"
    "    {\n"
    "      name: 'Osso Buco alla Milanese',\n"
    "      category: 'Secondi Piatti',\n"
    "      price: '$48',\n"
    "      description: 'Slow-braised cross-cut veal shank in white wine, aromatic vegetables, and gremolata over saffron risotto.',\n"
    "      image: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80'\n"
    "    },\n"
    "    {\n"
    "      name: 'Tiramisù Tradizionale',\n"
    "      category: 'Dolci',\n"
    "      price: '$16',\n"
    "      description: 'Layered Savoiardi biscuits infused with single-origin Italian espresso and aged Marsala, topped with sweet mascarpone cream.',\n"
    "      image: 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80'\n"
    "    }\n"
    "  ];\n\n"
    "  return (\n"
    "    <section id=\"dishes\" className=\"py-24 px-6 max-w-7xl mx-auto\">\n"
    "      <div className=\"text-center space-y-4 mb-16\">\n"
    "        <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Chef's Selections</span>\n"
    "        <h2 className=\"text-3xl sm:text-5xl font-serif font-bold text-stone-100\">Signature Culinary Creations</h2>\n"
    "        <p className=\"text-stone-400 max-w-xl mx-auto text-sm\">Handcrafted daily with imported DOP ingredients, organic herbs, and wood-fired perfection.</p>\n"
    "      </div>\n"
    "      <div className=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8\">\n"
    "        {dishes.map((item, idx) => (\n"
    "          <div key={idx} className=\"culinary-card rounded-2xl overflow-hidden group flex flex-col justify-between\">\n"
    "            <div className=\"relative h-56 overflow-hidden\">\n"
    "              <img src={item.image} alt={item.name} className=\"w-full h-full object-cover group-hover:scale-110 transition-transform duration-500\" />\n"
    "              <span className=\"absolute top-3 right-3 px-3 py-1 text-xs font-bold text-stone-950 bg-amber-400 rounded-full shadow-md\">{item.price}</span>\n"
    "            </div>\n"
    "            <div className=\"p-6 space-y-3 flex-1 flex flex-col justify-between\">\n"
    "              <div>\n"
    "                <span className=\"text-[11px] font-medium text-amber-400 uppercase tracking-wider\">{item.category}</span>\n"
    "                <h3 className=\"text-xl font-serif font-bold text-stone-100 mt-1\">{item.name}</h3>\n"
    "                <p className=\"text-xs text-stone-400 mt-2 leading-relaxed\">{item.description}</p>\n"
    "              </div>\n"
    "            </div>\n"
    "          </div>\n"
    "        ))}\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

menu_tsx = (
    "import React, { useState } from 'react';\n\n"
    "export default function MenuCategories() {\n"
    "  const [activeTab, setActiveTab] = useState('Antipasti');\n"
    "  const categories = {\n"
    "    Antipasti: [\n"
    "      { name: 'Burrata Pugliese con Prosciutto di Parma', price: '$22', desc: 'Creamy burrata, 24-month aged prosciutto, roasted figs, balsamic glaze.' },\n"
    "      { name: 'Carpaccio di Manzo', price: '$24', desc: 'Thinly sliced prime beef filet, wild arugula, capers, Parmigiano shavings.' }\n"
    "    ],\n"
    "    Primi: [\n"
    "      { name: 'Pappardelle al Cinghiale', price: '$32', desc: 'Wide ribbon pasta, slow-simmered Tuscan wild boar ragù, fresh rosemary.' },\n"
    "      { name: 'Gnocchi alla Sorrentina', price: '$28', desc: 'Handmade potato gnocchi, San Marzano tomato sauce, melted fior di latte.' }\n"
    "    ],\n"
    "    Secondi: [\n"
    "      { name: 'Bistecca alla Fiorentina (800g)', price: '$95', desc: 'Dry-aged T-bone steak grilled over oak charcoal, rosemary salt, olive oil.' },\n"
    "      { name: 'Brunello di Montalcino DOCG', price: '$120/btl', desc: '2016 Vintage Tuscan Sangiovese with notes of black cherry and oak.' }\n"
    "    ]\n"
    "  };\n\n"
    "  return (\n"
    "    <section id=\"menu\" className=\"py-20 px-6 bg-stone-900/40 border-y border-stone-800/60\">\n"
    "      <div className=\"max-w-5xl mx-auto space-y-12\">\n"
    "        <div className=\"text-center space-y-3\">\n"
    "          <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Fine Dining Menu</span>\n"
    "          <h2 className=\"text-3xl sm:text-4xl font-serif font-bold text-stone-100\">Explore Full Culinary Menu</h2>\n"
    "        </div>\n"
    "        <div className=\"flex justify-center gap-4\">\n"
    "          {Object.keys(categories).map((tab) => (\n"
    "            <button key={tab} onClick={() => setActiveTab(tab)} className={`px-6 py-2.5 text-xs font-bold uppercase tracking-wider rounded-full transition-all ${activeTab === tab ? 'bg-amber-500 text-stone-950 shadow-lg' : 'bg-stone-900 text-stone-300 border border-stone-800 hover:border-amber-500/50'}`}>\n"
    "              {tab}\n"
    "            </button>\n"
    "          ))}\n"
    "        </div>\n"
    "        <div className=\"grid grid-cols-1 md:grid-cols-2 gap-6 pt-4\">\n"
    "          {categories[activeTab].map((dish, i) => (\n"
    "            <div key={i} className=\"p-6 rounded-xl bg-stone-900/70 border border-stone-800 flex justify-between gap-4\">\n"
    "              <div>\n"
    "                <h4 className=\"font-serif font-bold text-stone-100 text-lg\">{dish.name}</h4>\n"
    "                <p className=\"text-xs text-stone-400 mt-1 leading-relaxed\">{dish.desc}</p>\n"
    "              </div>\n"
    "              <span className=\"text-base font-serif font-bold text-amber-400\">{dish.price}</span>\n"
    "            </div>\n"
    "          ))}\n"
    "        </div>\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

story_tsx = (
    "import React from 'react';\n\n"
    "export default function RestaurantStory() {\n"
    "  return (\n"
    "    <section id=\"story\" className=\"py-24 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-14\">\n"
    "      <div className=\"flex-1 space-y-6 text-left\">\n"
    "        <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Our Tuscan Heritage</span>\n"
    "        <h2 className=\"text-3xl sm:text-5xl font-serif font-bold text-stone-100 leading-tight\">A Legacy of Passion &amp; Authentic Italian Flavors</h2>\n"
    "        <p className=\"text-stone-300 text-base leading-relaxed font-light\">\n"
    "          Founded by Executive Chef Marco Rossi, Bella Tavola brings centuries-old Italian gastronomy to life. Every morning, our artisans hand-roll fresh tagliolini and ravioli using stone-ground Italian wheat flour and organic farm eggs.\n"
    "        </p>\n"
    "        <div className=\"grid grid-cols-2 gap-6 pt-4 text-stone-200 text-xs font-serif\">\n"
    "          <div className=\"p-4 rounded-xl bg-stone-900/60 border border-stone-800\">\n"
    "            <span className=\"text-2xl font-bold text-amber-400 block mb-1\">🇮🇹 DOP Imports</span>\n"
    "            Parmigiano Reggiano, San Marzano DOP, cold-pressed Tuscan olive oil.\n"
    "          </div>\n"
    "          <div className=\"p-4 rounded-xl bg-stone-900/60 border border-stone-800\">\n"
    "            <span className=\"text-2xl font-bold text-amber-400 block mb-1\">🪵 Oak Oven</span>\n"
    "            Custom Neapolitan brick wood oven reaching 900°F.\n"
    "          </div>\n"
    "        </div>\n"
    "      </div>\n"
    "      <div className=\"flex-1 w-full\">\n"
    "        <div className=\"rounded-2xl overflow-hidden border border-amber-900/30 shadow-2xl relative\">\n"
    "          <img src=\"https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=80\" alt=\"Bella Tavola Dining Room Ambience\" className=\"w-full h-full object-cover\" />\n"
    "        </div>\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

gallery_tsx = (
    "import React from 'react';\n\n"
    "export default function AmbienceGallery() {\n"
    "  const imgs = [\n"
    "    { url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80', cap: 'Candlelit Dining Room' },\n"
    "    { url: 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80', cap: 'Tuscan Wine Cellar' },\n"
    "    { url: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80', cap: 'Open Kitchen & Wood Oven' }\n"
    "  ];\n"
    "  return (\n"
    "    <section id=\"gallery\" className=\"py-20 px-6 max-w-7xl mx-auto space-y-12\">\n"
    "      <div className=\"text-center space-y-3\">\n"
    "        <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Atmosphere</span>\n"
    "        <h2 className=\"text-3xl sm:text-4xl font-serif font-bold text-stone-100\">Dining Ambience Gallery</h2>\n"
    "      </div>\n"
    "      <div className=\"grid grid-cols-1 md:grid-cols-3 gap-6\">\n"
    "        {imgs.map((item, idx) => (\n"
    "          <div key={idx} className=\"relative h-64 rounded-2xl overflow-hidden group border border-stone-800\">\n"
    "            <img src={item.url} alt={item.cap} className=\"w-full h-full object-cover group-hover:scale-110 transition-transform duration-500\" />\n"
    "            <div className=\"absolute inset-0 bg-stone-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4\">\n"
    "              <span className=\"text-xs font-serif font-bold text-amber-300\">{item.cap}</span>\n"
    "            </div>\n"
    "          </div>\n"
    "        ))}\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

hours_tsx = (
    "import React from 'react';\n\n"
    "export default function OpeningHoursLocation() {\n"
    "  return (\n"
    "    <section id=\"hours\" className=\"py-20 px-6 bg-stone-900/50 border-t border-stone-800\">\n"
    "      <div className=\"max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 text-left\">\n"
    "        <div className=\"space-y-6\">\n"
    "          <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Dining Hours</span>\n"
    "          <h3 className=\"text-3xl font-serif font-bold text-stone-100\">Opening Schedule</h3>\n"
    "          <div className=\"space-y-3 text-sm text-stone-300\">\n"
    "            <div className=\"flex justify-between pb-2 border-b border-stone-800\"><span>Monday — Thursday</span><span className=\"font-serif text-amber-400\">5:00 PM — 10:00 PM</span></div>\n"
    "            <div className=\"flex justify-between pb-2 border-b border-stone-800\"><span>Friday — Saturday</span><span className=\"font-serif text-amber-400\">4:30 PM — 11:00 PM</span></div>\n"
    "            <div className=\"flex justify-between pb-2 border-b border-stone-800\"><span>Sunday Brunch &amp; Dinner</span><span className=\"font-serif text-amber-400\">12:00 PM — 9:30 PM</span></div>\n"
    "          </div>\n"
    "        </div>\n"
    "        <div className=\"space-y-6\">\n"
    "          <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Location &amp; Contact</span>\n"
    "          <h3 className=\"text-3xl font-serif font-bold text-stone-100\">Find Bella Tavola</h3>\n"
    "          <div className=\"space-y-2 text-sm text-stone-300\">\n"
    "            <p className=\"font-serif font-semibold text-amber-200\">📍 450 Via Toscana Boulevard, Culinary District</p>\n"
    "            <p>📞 Phone Reservations: +1 (555) 835-5282</p>\n"
    "            <p>✉ Email: reservations@bellatavola.com</p>\n"
    "            <p className=\"text-xs text-stone-400 pt-2\">Valet parking available at restaurant main entrance.</p>\n"
    "          </div>\n"
    "        </div>\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

reservation_tsx = (
    "import React, { useState } from 'react';\n\n"
    "export default function TableReservation() {\n"
    "  const [submitted, setSubmitted] = useState(false);\n"
    "  const handleSubmit = (e: React.FormEvent) => {\n"
    "    e.preventDefault();\n"
    "    setSubmitted(true);\n"
    "  };\n"
    "  return (\n"
    "    <section id=\"reservation\" className=\"py-24 px-6 max-w-4xl mx-auto text-center\">\n"
    "      <div className=\"culinary-panel p-8 sm:p-12 rounded-3xl space-y-8 shadow-2xl border border-amber-500/30\">\n"
    "        <div className=\"space-y-3\">\n"
    "          <span className=\"text-xs font-semibold uppercase tracking-widest text-amber-400\">Table Reservation</span>\n"
    "          <h2 className=\"text-3xl sm:text-4xl font-serif font-bold text-stone-100\">Reserve Your Table</h2>\n"
    "          <p className=\"text-stone-300 text-sm max-w-lg mx-auto\">Select party size, date, and preferred dining time for an unforgettable evening.</p>\n"
    "        </div>\n"
    "        {submitted ? (\n"
    "          <div className=\"p-6 rounded-2xl bg-amber-950/60 border border-amber-500/50 text-amber-300 font-serif text-lg\">\n"
    "            ✓ Table Reservation Confirmed! We look forward to welcoming you at Bella Tavola.\n"
    "          </div>\n"
    "        ) : (\n"
    "          <form onSubmit={handleSubmit} className=\"grid grid-cols-1 sm:grid-cols-2 gap-5 text-left\">\n"
    "            <div>\n"
    "              <label className=\"block text-xs font-medium text-stone-300 uppercase tracking-wider mb-2\">Guest Name</label>\n"
    "              <input required type=\"text\" placeholder=\"Giovanni Rossi\" className=\"w-full px-4 py-3 rounded-xl bg-stone-900 border border-stone-700 text-stone-100 text-sm focus:border-amber-400 focus:outline-none\" />\n"
    "            </div>\n"
    "            <div>\n"
    "              <label className=\"block text-xs font-medium text-stone-300 uppercase tracking-wider mb-2\">Phone / Email</label>\n"
    "              <input required type=\"text\" placeholder=\"giovanni@example.com\" className=\"w-full px-4 py-3 rounded-xl bg-stone-900 border border-stone-700 text-stone-100 text-sm focus:border-amber-400 focus:outline-none\" />\n"
    "            </div>\n"
    "            <div>\n"
    "              <label className=\"block text-xs font-medium text-stone-300 uppercase tracking-wider mb-2\">Party Size</label>\n"
    "              <select className=\"w-full px-4 py-3 rounded-xl bg-stone-900 border border-stone-700 text-stone-100 text-sm focus:border-amber-400 focus:outline-none\">\n"
    "                <option>2 Guests</option>\n"
    "                <option>4 Guests</option>\n"
    "                <option>6 Guests</option>\n"
    "                <option>8+ Guests</option>\n"
    "              </select>\n"
    "            </div>\n"
    "            <div>\n"
    "              <label className=\"block text-xs font-medium text-stone-300 uppercase tracking-wider mb-2\">Preferred Date &amp; Time</label>\n"
    "              <input required type=\"text\" placeholder=\"Tonight at 7:30 PM\" className=\"w-full px-4 py-3 rounded-xl bg-stone-900 border border-stone-700 text-stone-100 text-sm focus:border-amber-400 focus:outline-none\" />\n"
    "            </div>\n"
    "            <div className=\"sm:col-span-2 pt-4\">\n"
    "              <button type=\"submit\" className=\"w-full py-4 text-sm font-bold uppercase tracking-wider text-stone-950 bg-gradient-to-r from-amber-400 via-amber-500 to-amber-600 rounded-xl shadow-xl hover:scale-[1.01] transition-all\">\n"
    "                Confirm Reservation\n"
    "              </button>\n"
    "            </div>\n"
    "          </form>\n"
    "        )}\n"
    "      </div>\n"
    "    </section>\n"
    "  );\n"
    "}\n"
)

footer_tsx = (
    "import React from 'react';\n\n"
    "export default function Footer() {\n"
    "  return (\n"
    "    <footer className=\"py-12 px-6 bg-stone-950 border-t border-stone-900 text-stone-400 text-xs\">\n"
    "      <div className=\"max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4\">\n"
    "        <div className=\"flex items-center gap-2 font-serif font-bold text-amber-400 text-sm\">\n"
    "          <span>⚜</span> BELLA TAVOLA RISTORANTE ITALIANO\n"
    "        </div>\n"
    "        <p>© 2026 Bella Tavola. All rights reserved.</p>\n"
    "        <a href=\"#hero\" className=\"text-amber-400 hover:underline\">Back to top ↑</a>\n"
    "      </div>\n"
    "    </footer>\n"
    "  );\n"
    "}\n"
)

app_tsx = (
    "import React from 'react';\n"
    "import Navbar from './components/Navbar';\n"
    "import HeroBanner from './components/HeroBanner';\n"
    "import SignatureDishes from './components/SignatureDishes';\n"
    "import MenuCategories from './components/MenuCategories';\n"
    "import RestaurantStory from './components/RestaurantStory';\n"
    "import AmbienceGallery from './components/AmbienceGallery';\n"
    "import OpeningHoursLocation from './components/OpeningHoursLocation';\n"
    "import TableReservation from './components/TableReservation';\n"
    "import Footer from './components/Footer';\n\n"
    "export default function App() {\n"
    "  return (\n"
    "    <div className=\"min-h-screen bg-stone-950 text-stone-100 font-sans selection:bg-amber-500 selection:text-stone-950\">\n"
    "      <Navbar />\n"
    "      <HeroBanner />\n"
    "      <SignatureDishes />\n"
    "      <MenuCategories />\n"
    "      <RestaurantStory />\n"
    "      <AmbienceGallery />\n"
    "      <OpeningHoursLocation />\n"
    "      <TableReservation />\n"
    "      <Footer />\n"
    "    </div>\n"
    "  );\n"
    "}\n"
)

readme_md = (
    "# Bella Tavola — Ristorante Italiano Classico\n\n"
    "A luxurious, modern website built for Bella Tavola Italian Restaurant featuring authentic food photography, signature dishes, fine dining menu filter, culinary story, gallery, location hours, and table reservation CTA.\n"
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
    "src/components/SignatureDishes.tsx": dishes_tsx,
    "src/components/MenuCategories.tsx": menu_tsx,
    "src/components/RestaurantStory.tsx": story_tsx,
    "src/components/AmbienceGallery.tsx": gallery_tsx,
    "src/components/OpeningHoursLocation.tsx": hours_tsx,
    "src/components/TableReservation.tsx": reservation_tsx,
    "src/components/Footer.tsx": footer_tsx,
    "src/App.tsx": app_tsx,
    "README.md": readme_md
}

from tools.coding.workspace_manager import WorkspaceManager
ws = WorkspaceManager.get_instance()

for rel_path, content in files_dict.items():
    ws.write_workspace_file(output_dir, rel_path, content)

print(f"[FILES PERSISTED] {len(files_dict)} project files written to disk at {output_dir}.")

# 3. Production Build
from tools.coding.website_deployer import LocalPreviewDeployer
is_built, build_msg = LocalPreviewDeployer.execute_production_build(output_dir)
print(f"[BUILD STATUS] {'SUCCESS' if is_built else 'FAILED'}: {build_msg}")

# 4. Start Local Preview Server
from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
url, port = server.start_preview(output_dir, port=5177, open_browser=False)
print(f"[LOCAL PREVIEW SERVER] Active at {url}")

# 5. Evaluate Visual QA
from tools.coding.website_visual_qa import WebsiteVisualQA
passed, issues = WebsiteVisualQA.evaluate_website(output_dir, url, website_type="luxurious_italian_restaurant")
print(f"[VISUAL QA EVALUATION] Status: {'PASS' if passed else 'FAIL'}, Issues: {issues}")

t_end = time.perf_counter() - t_start
print(f"Total Execution Duration: {t_end:.2f}s")
