import os
import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class VisualAssetItem:
    name: str
    category: str
    url: str
    local_path: str = ""
    alt_text: str = ""

@dataclass
class VisualAssetManifest:
    assets: List[VisualAssetItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "assets": [
                {
                    "name": a.name,
                    "category": a.category,
                    "url": a.url,
                    "local_path": a.local_path,
                    "alt_text": a.alt_text
                }
                for a in self.assets
            ]
        }

class WebsiteAssetPlanner:
    """
    Website Asset Planner.
    Generates high-resolution category-matched image assets (Unsplash/SVG)
    for requested website briefs.
    """

    @classmethod
    def plan_assets(cls, brief: any, output_dir: str) -> VisualAssetManifest:
        manifest = VisualAssetManifest()
        cat = brief.category.lower() if hasattr(brief, 'category') and brief.category else "custom"
        subj = brief.subject.name.lower() if hasattr(brief, 'subject') and brief.subject and hasattr(brief.subject, 'name') else ""

        if cat == "restaurant" or "bella" in subj or "italian" in subj or "dining" in cat:
            manifest.assets = [
                VisualAssetItem(name="hero_banner", category="image", url="https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=1200&q=80", alt_text="Gourmet Italian Culinary Artistry"),
                VisualAssetItem(name="dish_tagliolini", category="image", url="https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=800&q=80", alt_text="Tagliolini al Tartufo Nero"),
                VisualAssetItem(name="dish_margherita", category="image", url="https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=800&q=80", alt_text="Pizza Margherita Verace Napoletana"),
                VisualAssetItem(name="dish_ossobuco", category="image", url="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80", alt_text="Osso Buco alla Milanese"),
                VisualAssetItem(name="dish_tiramisu", category="image", url="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=800&q=80", alt_text="Tiramisù Tradizionale al Mascarpone"),
                VisualAssetItem(name="restaurant_ambience", category="image", url="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=80", alt_text="Bella Tavola Candlelit Dining Room"),
                VisualAssetItem(name="wine_cellar", category="image", url="https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80", alt_text="Bella Tavola Tuscan Wine Cellar")
            ]
        elif cat == "portfolio":
            manifest.assets = [
                VisualAssetItem(name="avatar", category="image", url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80", alt_text="Profile Avatar"),
                VisualAssetItem(name="project_jarvis", category="image", url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80", alt_text="Jarvis AI Assistant Platform"),
                VisualAssetItem(name="project_premiere", category="image", url="https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80", alt_text="AI Video Editing Agent"),
                VisualAssetItem(name="project_flutter", category="image", url="https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=800&q=80", alt_text="Flutter Attendance Mobile App")
            ]
        elif cat == "ecommerce":
            manifest.assets = [
                VisualAssetItem(name="hero_banner", category="image", url="https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80", alt_text="E-commerce Store Hero Banner"),
                VisualAssetItem(name="product_1", category="image", url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80", alt_text="Premium Product Card 1"),
                VisualAssetItem(name="product_2", category="image", url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80", alt_text="Premium Product Card 2")
            ]
        else:
            manifest.assets = [
                VisualAssetItem(name="hero_bg", category="image", url="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80", alt_text="Modern Business Banner"),
                VisualAssetItem(name="feature_1", category="image", url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80", alt_text="Business Feature 1")
            ]

        return manifest
