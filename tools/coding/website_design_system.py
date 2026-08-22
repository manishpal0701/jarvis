import json
from dataclasses import dataclass, field
from typing import Dict, Any
from ai.model_router import ModelRouter

@dataclass
class WebsiteDesignSystem:
    theme_name: str = "dark_developer"
    primary_color: str = "#06b6d4"      # Cyan 500
    secondary_color: str = "#6366f1"    # Indigo 500
    accent_color: str = "#10b981"       # Emerald 500
    background_color: str = "#020617"   # Slate 950
    surface_color: str = "#0f172a"      # Slate 900
    text_primary: str = "#f8fafc"       # Slate 50
    text_secondary: str = "#cbd5e1"     # Slate 300
    border_color: str = "#1e293b"       # Slate 800
    font_heading: str = "Inter, system-ui, sans-serif"
    font_body: str = "Inter, system-ui, sans-serif"
    font_mono: str = "Fira Code, monospace"
    border_radius: str = "1rem"
    glassmorphism_class: str = "glass-panel"
    card_hover_class: str = "glass-card"
    button_primary_class: str = "px-6 py-3.5 text-sm font-bold text-slate-950 bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-400 rounded-xl shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-95 transition-all"
    button_secondary_class: str = "px-6 py-3.5 text-sm font-semibold text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 rounded-xl transition-all"
    css_variables: Dict[str, str] = field(default_factory=dict)

    def to_css_block(self) -> str:
        vars_str = "\n".join([f"  --{k}: {v};" for k, v in self.css_variables.items()])
        return f":root {{\n{vars_str}\n}}"

class WebsiteDesignSystemGenerator:
    """
    Website Design System Generator Agent.
    Uses qwen3:8b model to output a cohesive category-aligned WebsiteDesignSystem
    before code generation begins.
    """

    @classmethod
    def generate_design_system(cls, research_spec: any, prompt: str) -> WebsiteDesignSystem:
        model_name = ModelRouter.get_instance().get_model_for_task("website_design")
        wtype = getattr(research_spec, "website_type", "portfolio")

        if wtype in ("developer_portfolio", "portfolio") or "developer" in prompt.lower() or "engineer" in prompt.lower():
            css_vars = {
                "background": "#020617",
                "surface": "#0f172a",
                "primary": "#06b6d4",
                "secondary": "#6366f1",
                "accent": "#10b981",
                "text-primary": "#f8fafc",
                "text-secondary": "#cbd5e1",
                "border": "#1e293b",
                "radius": "1rem"
            }
            return WebsiteDesignSystem(
                theme_name="dark_developer",
                primary_color="#06b6d4",
                secondary_color="#6366f1",
                accent_color="#10b981",
                background_color="#020617",
                surface_color="#0f172a",
                text_primary="#f8fafc",
                text_secondary="#cbd5e1",
                border_color="#1e293b",
                css_variables=css_vars
            )

        elif wtype == "restaurant":
            css_vars = {
                "background": "#1c1917",
                "surface": "#292524",
                "primary": "#f59e0b",
                "secondary": "#d97706",
                "accent": "#ef4444",
                "text-primary": "#fafaf9",
                "text-secondary": "#e7e5e4",
                "border": "#44403c",
                "radius": "0.75rem"
            }
            return WebsiteDesignSystem(
                theme_name="warm_culinary",
                primary_color="#f59e0b",
                secondary_color="#d97706",
                accent_color="#ef4444",
                background_color="#1c1917",
                surface_color="#292524",
                text_primary="#fafaf9",
                text_secondary="#e7e5e4",
                border_color="#44403c",
                button_primary_class="px-6 py-3 text-sm font-bold text-stone-950 bg-amber-500 hover:bg-amber-400 rounded-lg shadow-lg transition-all",
                button_secondary_class="px-6 py-3 text-sm font-semibold text-stone-200 bg-stone-900 border border-stone-700 hover:bg-stone-800 rounded-lg transition-all",
                css_variables=css_vars
            )

        elif wtype == "saas_product":
            css_vars = {
                "background": "#0f172a",
                "surface": "#1e293b",
                "primary": "#4f46e5",
                "secondary": "#06b6d4",
                "accent": "#10b981",
                "text-primary": "#f8fafc",
                "text-secondary": "#94a3b8",
                "border": "#334155",
                "radius": "0.75rem"
            }
            return WebsiteDesignSystem(
                theme_name="modern_saas",
                primary_color="#4f46e5",
                secondary_color="#06b6d4",
                accent_color="#10b981",
                background_color="#0f172a",
                surface_color="#1e293b",
                text_primary="#f8fafc",
                text_secondary="#94a3b8",
                border_color="#334155",
                css_variables=css_vars
            )

        else:
            css_vars = {
                "background": "#090d16",
                "surface": "#111827",
                "primary": "#3b82f6",
                "secondary": "#6366f1",
                "accent": "#10b981",
                "text-primary": "#f9fafb",
                "text-secondary": "#d1d5db",
                "border": "#1f2937",
                "radius": "0.75rem"
            }
            return WebsiteDesignSystem(
                theme_name="clean_commercial",
                primary_color="#3b82f6",
                secondary_color="#6366f1",
                accent_color="#10b981",
                background_color="#090d16",
                surface_color="#111827",
                text_primary="#f9fafb",
                text_secondary="#d1d5db",
                border_color="#1f2937",
                css_variables=css_vars
            )
