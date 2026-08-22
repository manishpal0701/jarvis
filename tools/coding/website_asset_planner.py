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
    Generates fallback visual assets and placeholder image URLs (Unsplash/SVG)
    for requested website briefs when local assets are absent.
    """

    @classmethod
    def plan_assets(cls, brief: any, output_dir: str) -> VisualAssetManifest:
        manifest = VisualAssetManifest()
        cat = brief.category.lower() if hasattr(brief, 'category') and brief.category else "custom"

        if cat == "portfolio":
            manifest.assets = [
                VisualAssetItem(name="avatar", category="image", url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80", alt_text="Manish Profile Avatar"),
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
        elif cat == "restaurant":
            manifest.assets = [
                VisualAssetItem(name="hero_dish", category="image", url="https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80", alt_text="Delicious Special Dish Hero"),
                VisualAssetItem(name="dish_1", category="image", url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80", alt_text="Special Pizza Menu Dish"),
                VisualAssetItem(name="dish_2", category="image", url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80", alt_text="Gourmet Burger Menu Item")
            ]
        else:
            manifest.assets = [
                VisualAssetItem(name="hero_bg", category="image", url="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80", alt_text="Modern Business Banner"),
                VisualAssetItem(name="feature_1", category="image", url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80", alt_text="Business Feature 1")
            ]

        return manifest
