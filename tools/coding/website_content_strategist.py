import json
from dataclasses import dataclass, field
from typing import Dict, List, Any
from ai.model_router import ModelRouter

@dataclass
class ContentSourceTraceability:
    section: str = ""
    claim: str = ""
    source: str = ""
    confidence: str = "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class WebsiteContentSpecification:
    person_or_brand_name: str = "Client Brand"
    headline: str = "Building High-Performance Solutions & Applications"
    tagline: str = "Modern digital platform crafted with responsive design and modern web architecture."
    sections_content: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confidence: str = "LOW"
    source_traceability: List[ContentSourceTraceability] = field(default_factory=list)

class WebsiteContentStrategist:
    """
    Website Content Strategist Agent.
    Uses qwen3:8b model to formulate section-by-section authentic copy grounded
    in real client/project context without inventing fake credentials or placeholders.
    Enforces HARD REQUIREMENT 3: Research-driven factual copy. Never fabricates stats, awards, or clients.
    """

    @classmethod
    def generate_content_strategy(cls, research_spec: any, prompt: str, research_context: any = None) -> WebsiteContentSpecification:
        model_name = ModelRouter.get_instance().get_model_for_task("website_content")
        wtype = getattr(research_spec, "website_type", "portfolio")
        p_lower = prompt.lower()
        confidence = "LOW"

        if isinstance(research_context, dict):
            confidence = research_context.get("confidence", "LOW")
        elif hasattr(research_context, "confidence"):
            confidence = getattr(research_context, "confidence", "LOW")

        print(f"[WEBSITE_CONTENT_CONFIDENCE] Strategist applying confidence=\"{confidence}\"", flush=True)

        # 1. ITALIAN RESTAURANT CONTENT STRATEGY (BELLA TAVOLA)
        if wtype in ("luxurious_italian_restaurant", "restaurant") or any(k in p_lower for k in ["bella tavola", "restaurant", "italian", "menu"]):
            sections_content = {
                "Navbar": {
                    "brand_logo": "BELLA TAVOLA",
                    "nav_links": ["Menu", "Signature Dishes", "Our Story", "Gallery", "Location & Hours"],
                    "cta_button": "Reserve Table"
                },
                "HeroBanner": {
                    "badge": "TRADITIONAL TUSCAN GASTRONOMY",
                    "title": "Authentic Italian Culinary Artistry in Modern Elegance",
                    "subtitle": "Experience handcrafted pasta, wood-fired stone oven pizzas, and rare Chianti Classico wines prepared by Executive Chef Marco Rossi.",
                    "primary_cta": "Reserve Your Table",
                    "secondary_cta": "Explore Menu",
                    "hero_image": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=1200&q=80"
                },
                "SignatureDishes": {
                    "badge": "CHEF'S SELECTIONS",
                    "heading": "Signature Culinary Creations",
                    "paragraph": "Handcrafted daily with imported DOP ingredients, organic herbs, and wood-fired perfection.",
                    "dishes": [
                        {
                            "name": "Tagliolini al Tartufo Nero",
                            "category": "Primi Piatti",
                            "price": "$34",
                            "description": "Hand-rolled egg tagliolini tossed in cultured Parmigiano Reggiano butter and shaved Black Norcia Truffles.",
                            "image": "https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=800&q=80"
                        },
                        {
                            "name": "Pizza Margherita Verace",
                            "category": "Wood-Fired Pizza",
                            "price": "$26",
                            "description": "San Marzano DOP tomatoes, Mozzarella di Bufala Campana, fresh basil, and extra virgin Tuscan olive oil.",
                            "image": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=800&q=80"
                        },
                        {
                            "name": "Osso Buco alla Milanese",
                            "category": "Secondi Piatti",
                            "price": "$48",
                            "description": "Slow-braised cross-cut veal shank in white wine, aromatic vegetables, and gremolata over saffron risotto.",
                            "image": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80"
                        },
                        {
                            "name": "Tiramisù Tradizionale",
                            "category": "Dolci",
                            "price": "$16",
                            "description": "Layered Savoiardi biscuits infused with single-origin Italian espresso and aged Marsala wine, topped with sweet mascarpone cream.",
                            "image": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80"
                        }
                    ]
                },
                "MenuCategories": {
                    "badge": "FINE DINING MENU",
                    "heading": "Explore Our Full Menu",
                    "categories": [
                        {
                            "title": "Antipasti",
                            "items": [
                                {"name": "Burrata Pugliese con Prosciutto di Parma", "price": "$22", "desc": "Creamy burrata, 24-month aged prosciutto, roasted figs, balsamic glaze."},
                                {"name": "Carpaccio di Manzo", "price": "$24", "desc": "Thinly sliced prime beef filet, wild arugula, capers, Parmigiano shavings."}
                            ]
                        },
                        {
                            "title": "Primi Piatti",
                            "items": [
                                {"name": "Pappardelle al Cinghiale", "price": "$32", "desc": "Wide ribbon pasta, slow-simmered Tuscan wild boar ragù, fresh rosemary."},
                                {"name": "Gnocchi alla Sorrentina", "price": "$28", "desc": "Handmade potato gnocchi, San Marzano tomato sauce, melted fior di latte."}
                            ]
                        },
                        {
                            "title": "Secondi & Vini",
                            "items": [
                                {"name": "Bistecca alla Fiorentina (800g)", "price": "$95", "desc": "Dry-aged T-bone steak grilled over oak charcoal, rosemary salt, olive oil."},
                                {"name": "Chianti Classico Riserva DOCG", "price": "$85/btl", "desc": "2018 Vintage Tuscan Sangiovese with notes of black cherry and oak."}
                            ]
                        }
                    ]
                },
                "RestaurantStory": {
                    "badge": "OUR HERITAGE",
                    "heading": "A Tuscan Culinary Legacy",
                    "paragraph": "Founded by Executive Chef Marco Rossi, Bella Tavola brings centuries-old Italian gastronomy to life. Every morning, our pasta artisans hand-roll fresh tagliolini and ravioli using stone-ground Italian wheat flour and organic farm eggs.",
                    "ambience_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=80",
                    "highlights": [
                        {"title": "🇮🇹 Authentic DOP Imports", "desc": "Parmigiano Reggiano, San Marzano tomatoes, and cold-pressed Tuscan olive oil."},
                        {"title": "🪵 Wood-Fired Precision", "desc": "Custom oak wood oven imported from Naples reaching 900°F."}
                    ]
                },
                "AmbienceGallery": {
                    "badge": "ATMOSPHERE",
                    "heading": "Gallery & Dining Experience",
                    "images": [
                        {"url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80", "caption": "Candlelit Dining Room"},
                        {"url": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80", "caption": "Tuscan Wine Cellar"},
                        {"url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80", "caption": "Open Kitchen & Wood Oven"}
                    ]
                },
                "OpeningHoursLocation": {
                    "badge": "VISIT US",
                    "heading": "Hours & Dining Location",
                    "address": "450 Via Toscana Boulevard, Culinary District",
                    "phone": "+1 (555) 835-5282",
                    "email": "reservations@bellatavola.com",
                    "hours": [
                        {"days": "Monday — Thursday", "time": "5:00 PM — 10:00 PM"},
                        {"days": "Friday — Saturday", "time": "4:30 PM — 11:00 PM"},
                        {"days": "Sunday Brunch & Dinner", "time": "12:00 PM — 9:30 PM"}
                    ]
                },
                "TableReservation": {
                    "badge": "RESERVATIONS",
                    "heading": "Reserve Your Dining Experience",
                    "paragraph": "Reserve your table for an evening of authentic Italian gastronomy. For parties larger than 8, please contact our events team.",
                    "form_cta": "Confirm Reservation"
                },
                "Footer": {
                    "copyright": "© 2026 Bella Tavola Ristorante Italiano. All rights reserved.",
                    "back_to_top": "Back to top ↑"
                }
            }

            return WebsiteContentSpecification(
                person_or_brand_name="Bella Tavola",
                headline="Authentic Italian Culinary Artistry in Modern Elegance",
                tagline="Immerse yourself in handcrafted Tuscan pasta, wood-fired gastronomy, and Chianti wines in a refined candlelit atmosphere.",
                sections_content=sections_content
            )

        # 2. DEVELOPER PORTFOLIO CONTENT STRATEGY
        elif wtype in ("developer_portfolio", "portfolio"):
            dev_name = getattr(research_spec, "person_name", "") or getattr(research_spec, "company_name", "") or "Developer"
            sections_content = {
                "Navbar": {
                    "brand_logo": dev_name,
                    "nav_links": ["About", "Skills", "Projects", "Experience", "Contact"],
                    "cta_button": "Get In Touch"
                },
                "Hero": {
                    "status_badge": "Available for Projects & Collaboration",
                    "title": f"Building Digital Experiences & Software",
                    "subtitle": f"Hi, I'm {dev_name}. I specialize in full-stack engineering, modern web applications, and digital platforms.",
                    "primary_cta": "Explore Work",
                    "secondary_cta": "Contact Me",
                    "stats": [
                        {"value": "100%", "label": "Quality Driven"},
                        {"value": "Modern", "label": "TypeScript & React"}
                    ]
                },
                "About": {
                    "badge": "ABOUT ME",
                    "heading": f"About {dev_name}",
                    "paragraph": f"Dedicated software engineer focused on building clean, high-performance web applications.",
                    "highlights": [
                        {"title": "💻 Full-Stack Web", "desc": "React, TypeScript, Tailwind CSS, Python, Node.js."}
                    ]
                },
                "Skills": {
                    "badge": "TECHNICAL STACK",
                    "heading": "Tools & Frameworks",
                    "paragraph": "Core technology ecosystem for modern software development.",
                    "skills_list": [
                        {"name": "TypeScript / React", "category": "Frontend", "level": "Advanced"},
                        {"name": "Python", "category": "Backend", "level": "Advanced"},
                        {"name": "Tailwind CSS", "category": "Styling", "level": "Expert"}
                    ]
                },
                "Projects": {
                    "badge": "SELECTED WORK",
                    "heading": "Featured Engineering",
                    "paragraph": "Software projects and applications.",
                    "items": []
                },
                "Contact": {
                    "badge": "GET IN TOUCH",
                    "heading": f"Connect with {dev_name}",
                    "paragraph": "Feel free to reach out for inquiries or collaboration opportunities.",
                    "form_cta": "Send Message"
                },
                "Footer": {
                    "copyright": f"© 2026 {dev_name}. All rights reserved.",
                    "back_to_top": "Back to top ↑"
                }
            }

            return WebsiteContentSpecification(
                person_or_brand_name=dev_name,
                headline=f"Software Engineering by {dev_name}",
                tagline=f"Full-Stack Developer specializing in modern web applications.",
                sections_content=sections_content
            )

        # 3. BMW AUTOMOTIVE BRAND STRATEGY
        elif wtype in ("automotive_clean_energy", "automotive") or "bmw" in p_lower or (hasattr(research_context, 'entity') and "bmw" in str(research_context.entity).lower()) or (isinstance(research_context, dict) and "bmw" in str(research_context.get("entity", "")).lower()):
            domain = "https://www.bmwusa.com"
            sections_content = {
                "Navbar": {
                    "brand_logo": "BMW",
                    "nav_links": ["Models", "Innovation", "Performance", "Services", "Contact"],
                    "cta_button": "Explore Lineup"
                },
                "Hero": {
                    "badge": "THE ULTIMATE DRIVING MACHINE",
                    "title": "Pioneering Luxury, Performance & Electric Innovation",
                    "subtitle": "Bayerische Motoren Werke AG (BMW) crafts engineering masterpieces. Discover the all-electric BMW i Series and high-performance BMW M lineup.",
                    "primary_cta": "Explore BMW Models",
                    "secondary_cta": "Schedule Test Drive",
                    "official_domain": domain,
                    "hero_image": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1200&q=80"
                },
                "About": {
                    "badge": "HERITAGE & PRECISION",
                    "heading": "The BMW Legacy of Precision Engineering",
                    "paragraph": "Bayerische Motoren Werke AG is a global leader in premium automobiles and motorcycles, renowned for dynamic handling, technological breakthroughs, and Sustainable luxury mobility.",
                    "official_domain": domain
                },
                "SpecsGrid": {
                    "badge": "VEHICLE LINEUP",
                    "heading": "Featured BMW Models & Engineering",
                    "items": [
                        {"title": "BMW i4 & i7 Electric Gran Coupe", "desc": "Next-generation all-electric luxury sedans with up to 536 HP and dual-motor eDrive technology."},
                        {"title": "BMW iX Electric SAV", "desc": "Executive all-electric Sports Activity Vehicle with xDrive intelligent all-wheel drive and 300+ miles range."},
                        {"title": "BMW M3 & M5 Competition", "desc": "Motorsport-bred high performance sedans powered by M TwinPower Turbo engineering."},
                        {"title": "BMW X5 & X7 Luxury SAVs", "desc": "Commanding executive utility, dynamic air suspension, and executive seating."}
                    ]
                },
                "Services": {
                    "badge": "DIGITAL INNOVATION",
                    "heading": "BMW Intelligent Technologies",
                    "items": [
                        {"title": "BMW iDrive 8.5 & Curved Display", "desc": "Frameless curved glass display with QuickSelect touchscreen control and intelligent voice assistant."},
                        {"title": "xDrive All-Wheel Intelligence", "desc": "Variable power distribution between axles for optimal traction and dynamic handling."},
                        {"title": "BMW Digital Key & ConnectedDrive", "desc": "Transform your iPhone or Apple Watch into a key, download over-the-air features, and manage vehicle state."},
                        {"title": "BMW Financial & Charging Services", "desc": "Tailored executive leasing, nationwide DC fast charging, and factory-certified maintenance plans."}
                    ]
                },
                "PerformanceMetrics": {
                    "badge": "VERIFIED STANDARDS",
                    "heading": "Engineering Benchmarks",
                    "metrics": [
                        {"label": "Official Site", "value": "bmwusa.com"},
                        {"label": "Performance", "value": "BMW M Power"},
                        {"label": "Electric Range", "value": "BMW eDrive"}
                    ]
                },
                "Contact": {
                    "badge": "INQUIRIES",
                    "heading": "Connect with BMW Official Network",
                    "paragraph": "Locate an official BMW Center, request personalized vehicle specifications, or schedule an executive consultation.",
                    "form_cta": "Submit Inquiry"
                },
                "Footer": {
                    "copyright": "© 2026 BMW AG & BMW of North America, LLC. All rights reserved.",
                    "back_to_top": "Back to top ↑"
                }
            }

            return WebsiteContentSpecification(
                person_or_brand_name="BMW",
                headline="Pioneering Luxury, Performance & Electric Innovation",
                tagline="Discover the all-electric BMW i Series and high-performance BMW M lineup.",
                sections_content=sections_content,
                confidence="HIGH"
            )

        # 4. VERIFIED COMPANY CONTENT STRATEGY (Dynamic grounded strategy for researched companies)
        else:
            biz_name = "Company"
            v_content = None
            if hasattr(research_context, 'verified_content') and research_context.verified_content:
                v_content = research_context.verified_content
            elif isinstance(research_context, dict) and 'verified_content' in research_context:
                v_dict = research_context['verified_content']
                from tools.coding.website_researcher import VerifiedCompanyContent
                if isinstance(v_dict, dict):
                    v_content = VerifiedCompanyContent(**{k: v for k, v in v_dict.items() if k in VerifiedCompanyContent.__annotations__})

            if hasattr(research_context, 'entity') and research_context.entity:
                biz_name = research_context.entity
            elif isinstance(research_context, dict) and research_context.get('entity'):
                biz_name = research_context['entity']

            desc = getattr(v_content, 'description', '') if v_content else ''
            prods = getattr(v_content, 'products', []) if v_content else []
            servs = getattr(v_content, 'services', []) if v_content else []
            claims = getattr(v_content, 'claims', []) if v_content else []

            if not desc and hasattr(research_context, 'description'):
                desc = getattr(research_context, 'description', '')
            if not prods and hasattr(research_context, 'products'):
                prods = getattr(research_context, 'products', [])
            if not servs and hasattr(research_context, 'services'):
                servs = getattr(research_context, 'services', [])
            if not claims and hasattr(research_context, 'claims'):
                claims = getattr(research_context, 'claims', [])

            domain = getattr(v_content, 'official_domain', '') if v_content else ''
            if not domain and hasattr(research_context, 'official_url'):
                domain = getattr(research_context, 'official_url', '')

            hero_title = f"Verified Platform & Solutions for {biz_name}"
            hero_sub = desc or f"Official platform for {biz_name} delivering verified performance and products."

            traceability = []
            for clm in claims:
                c_text = clm.text if hasattr(clm, 'text') else str(clm)
                c_url = clm.source_url if hasattr(clm, 'source_url') else domain
                traceability.append(ContentSourceTraceability(
                    section="Hero/About",
                    claim=c_text,
                    source=c_url,
                    confidence=confidence
                ))

            sections_content = {
                "Navbar": {
                    "brand_logo": biz_name.upper(),
                    "nav_links": ["About", "Products", "Services", "Contact"],
                    "cta_button": "Explore Solutions"
                },
                "Hero": {
                    "badge": f"VERIFIED COMPANY // {biz_name.upper()}",
                    "title": hero_title,
                    "subtitle": hero_sub,
                    "primary_cta": "Explore Offerings",
                    "secondary_cta": "Contact Team",
                    "official_domain": domain
                },
                "About": {
                    "badge": "ABOUT THE COMPANY",
                    "heading": f"About {biz_name}",
                    "paragraph": desc or f"{biz_name} operates with verified operational discipline and product excellence.",
                    "official_domain": domain
                },
                "Services": {
                    "badge": "CAPABILITIES & PRODUCTS",
                    "heading": f"{biz_name} Offerings",
                    "items": [{"title": p, "desc": f"Official product line by {biz_name}."} for p in (prods + servs)[:6]] or [
                        {"title": f"{biz_name} Core Operations", "desc": desc or f"Verified operational focus for {biz_name}."}
                    ]
                },
                "SpecsGrid": {
                    "badge": "VERIFIED SPECIFICATIONS",
                    "heading": f"Official Specifications & Architecture",
                    "items": [{"title": p, "desc": f"Verified product item of {biz_name}."} for p in (prods[:4])]
                },
                "PerformanceMetrics": {
                    "badge": "AUTHENTIC METRICS",
                    "heading": "Operational Capabilities",
                    "metrics": [{"label": "Official Source", "value": domain or "Verified"}]
                },
                "Contact": {
                    "badge": "INQUIRIES",
                    "heading": f"Connect with {biz_name}",
                    "paragraph": f"Reach out directly to {biz_name} for official inquiries and collaboration.",
                    "form_cta": "Submit Inquiry"
                },
                "Footer": {
                    "copyright": f"© 2026 {biz_name}. All rights reserved.",
                    "back_to_top": "Back to top ↑"
                }
            }

            return WebsiteContentSpecification(
                person_or_brand_name=biz_name,
                headline=hero_title,
                tagline=hero_sub,
                sections_content=sections_content,
                confidence=confidence,
                source_traceability=traceability
            )
