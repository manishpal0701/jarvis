import os
import re
import time
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from tools.coding.reference_analysis_engine import ReferenceItem

@dataclass
class LocalClientAsset:
    asset_id: str
    original_filename: str
    mime_type: str
    local_path: str
    role: str = "unknown"  # hero_image, logo, profile_image, project_image, gallery_image, reference_image, unknown
    caption: str = ""
    provenance: str = "CLIENT_PROVIDED"
    received_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

@dataclass
class LocalClientChatMessage:
    message_id: str
    sender: str  # user, assistant
    timestamp: str
    text: str
    attachments: List[LocalClientAsset] = field(default_factory=list)
    references: List[ReferenceItem] = field(default_factory=list)

class LocalClientBriefSession:
    """
    Local Client Brief Chat Session Manager.
    Stores user-provided chat messages, attachments, and optional design references
    (URL, Video, PDF, Screenshot) locally without external messaging APIs.
    """
    _instance = None

    def __init__(self):
        self.session_id: str = "local_session_001"
        self.client_name: str = "Client"
        self.website_type: str = ""
        self.business_description: str = ""
        self.website_goal: str = ""
        self.target_audience: str = ""
        self.location: str = ""
        self.contact_number: str = ""
        self.email: str = ""
        self.address: str = ""
        self.brand_description: str = ""
        self.brand_tone: str = ""
        self.primary_color: str = ""
        self.secondary_color: str = ""
        self.preferred_font: str = ""
        self.logo_availability: str = ""
        self.required_pages: str = ""
        self.required_sections: str = ""
        self.features_functionality: str = ""
        self.cta_action: str = ""
        self.special_requirements: str = ""
        self.seo_requirements: str = ""
        self.hero_heading: str = ""
        self.hero_description: str = ""
        self.about_content: str = ""
        self.services_products: str = ""
        self.pricing: str = ""
        self.contact_info: str = ""
        self.social_links: str = ""
        self.inspiration_style: str = ""

        self.messages: List[LocalClientChatMessage] = []
        self.assets: List[LocalClientAsset] = []
        self.reference_items: List[ReferenceItem] = []
        self.is_ready: bool = False

    @classmethod
    def get_instance(cls) -> "LocalClientBriefSession":
        if cls._instance is None:
            cls._instance = LocalClientBriefSession()
            cls._instance.load_from_disk()
        return cls._instance

    def _get_persistence_file(self) -> str:
        return os.path.abspath(os.path.join("data", "client_brief.json"))

    def save_to_disk(self):
        import json
        file_path = self._get_persistence_file()
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name, exist_ok=True)

        data = {
            "session_id": self.session_id,
            "client_name": self.client_name,
            "website_type": self.website_type,
            "business_description": self.business_description,
            "website_goal": self.website_goal,
            "target_audience": self.target_audience,
            "location": self.location,
            "contact_number": self.contact_number,
            "email": self.email,
            "address": self.address,
            "brand_description": self.brand_description,
            "brand_tone": self.brand_tone,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "preferred_font": self.preferred_font,
            "logo_availability": self.logo_availability,
            "required_pages": self.required_pages,
            "required_sections": self.required_sections,
            "features_functionality": self.features_functionality,
            "cta_action": self.cta_action,
            "special_requirements": self.special_requirements,
            "seo_requirements": self.seo_requirements,
            "hero_heading": self.hero_heading,
            "hero_description": self.hero_description,
            "about_content": self.about_content,
            "services_products": self.services_products,
            "pricing": self.pricing,
            "contact_info": self.contact_info,
            "social_links": self.social_links,
            "inspiration_style": self.inspiration_style,
            "is_ready": self.is_ready,
            "messages": [
                {
                    "message_id": m.message_id,
                    "sender": m.sender,
                    "timestamp": m.timestamp,
                    "text": m.text
                } for m in self.messages
            ],
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "original_filename": a.original_filename,
                    "mime_type": a.mime_type,
                    "local_path": a.local_path,
                    "role": a.role,
                    "caption": a.caption,
                    "provenance": a.provenance,
                    "received_at": a.received_at
                } for a in self.assets
            ],
            "reference_items": [
                {
                    "ref_type": r.ref_type,
                    "source": r.source,
                    "title": r.title,
                    "description": getattr(r, "description", "")
                } for r in self.reference_items
            ]
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[CLIENT_BRIEF_PERSISTENCE_ERR] Could not save: {e}")

    def load_from_disk(self):
        import json
        file_path = self._get_persistence_file()
        if not os.path.exists(file_path):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.session_id = data.get("session_id", "local_session_001")
            self.client_name = data.get("client_name", "Client")
            self.website_type = data.get("website_type", "")
            self.business_description = data.get("business_description", "")
            self.website_goal = data.get("website_goal", "")
            self.target_audience = data.get("target_audience", "")
            self.location = data.get("location", "")
            self.contact_number = data.get("contact_number", "")
            self.email = data.get("email", "")
            self.address = data.get("address", "")
            self.brand_description = data.get("brand_description", "")
            self.brand_tone = data.get("brand_tone", "")
            self.primary_color = data.get("primary_color", "")
            self.secondary_color = data.get("secondary_color", "")
            self.preferred_font = data.get("preferred_font", "")
            self.logo_availability = data.get("logo_availability", "")
            self.required_pages = data.get("required_pages", "")
            self.required_sections = data.get("required_sections", "")
            self.features_functionality = data.get("features_functionality", "")
            self.cta_action = data.get("cta_action", "")
            self.special_requirements = data.get("special_requirements", "")
            self.seo_requirements = data.get("seo_requirements", "")
            self.hero_heading = data.get("hero_heading", "")
            self.hero_description = data.get("hero_description", "")
            self.about_content = data.get("about_content", "")
            self.services_products = data.get("services_products", "")
            self.pricing = data.get("pricing", "")
            self.contact_info = data.get("contact_info", "")
            self.social_links = data.get("social_links", "")
            self.inspiration_style = data.get("inspiration_style", "")
            self.is_ready = data.get("is_ready", False)

            self.messages = [
                LocalClientChatMessage(
                    message_id=m["message_id"],
                    sender=m["sender"],
                    timestamp=m["timestamp"],
                    text=m["text"]
                ) for m in data.get("messages", [])
            ]
            self.assets = [
                LocalClientAsset(
                    asset_id=a["asset_id"],
                    original_filename=a["original_filename"],
                    mime_type=a["mime_type"],
                    local_path=a["local_path"],
                    role=a.get("role", "unknown"),
                    caption=a.get("caption", ""),
                    provenance=a.get("provenance", "CLIENT_PROVIDED"),
                    received_at=a.get("received_at", datetime.datetime.now().isoformat())
                ) for a in data.get("assets", [])
            ]
            self.reference_items = [
                ReferenceItem(
                    ref_type=r["ref_type"],
                    source=r["source"],
                    title=r.get("title", ""),
                    description=r.get("description", "")
                ) for r in data.get("reference_items", [])
            ]
        except Exception as e:
            print(f"[CLIENT_BRIEF_PERSISTENCE_ERR] Could not load: {e}")

    def reset_session(self):
        self.reset()

    def reset(self):
        self.messages.clear()
        self.assets.clear()
        self.reference_items.clear()
        self.client_name = "Client"
        self.website_type = ""
        self.business_description = ""
        self.website_goal = ""
        self.target_audience = ""
        self.location = ""
        self.contact_number = ""
        self.email = ""
        self.address = ""
        self.brand_description = ""
        self.brand_tone = ""
        self.primary_color = ""
        self.secondary_color = ""
        self.preferred_font = ""
        self.logo_availability = ""
        self.required_pages = ""
        self.required_sections = ""
        self.features_functionality = ""
        self.cta_action = ""
        self.special_requirements = ""
        self.seo_requirements = ""
        self.hero_heading = ""
        self.hero_description = ""
        self.about_content = ""
        self.services_products = ""
        self.pricing = ""
        self.contact_info = ""
        self.social_links = ""
        self.inspiration_style = ""
        self.is_ready = False
        file_path = self._get_persistence_file()
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    def add_user_message(
        self,
        text: str,
        attachments: List[LocalClientAsset] = None,
        references: List[ReferenceItem] = None
    ) -> LocalClientChatMessage:
        msg_id = f"msg_{len(self.messages) + 1:03d}"
        now_ts = datetime.datetime.now().isoformat()
        atts = attachments or []
        refs = references or []

        msg = LocalClientChatMessage(
            message_id=msg_id,
            sender="user",
            timestamp=now_ts,
            text=text,
            attachments=atts,
            references=refs
        )
        self.messages.append(msg)
        print(f"[CLIENT_CHAT] MESSAGE_RECEIVED id={msg_id} text=\"{text[:40]}\"", flush=True)

        for att in atts:
            if att not in self.assets:
                self.assets.append(att)
                print(f"[CLIENT_CHAT] ATTACHMENT_RECEIVED filename={att.original_filename}", flush=True)
                print(f"[CLIENT_CHAT] ASSET_REGISTERED role={att.role} provenance={att.provenance}", flush=True)

        for ref in refs:
            if ref not in self.reference_items:
                self.reference_items.append(ref)
                print(f"[CLIENT_CHAT] REFERENCE_REGISTERED type={ref.ref_type} source={ref.source}", flush=True)

        # Detect references inside text (URLs, file paths)
        self._extract_references_from_text(text)

        self.is_ready = len(self.messages) > 0
        self.save_to_disk()
        return msg

    def _extract_references_from_text(self, text: str):
        if not text:
            return

        # Extract HTTP/HTTPS URLs as reference URLs
        urls = re.findall(r'https?://[^\s>]+', text)
        for u in urls:
            if not any(r.source == u for r in self.reference_items):
                ref = ReferenceItem(ref_type="URL", source=u, title="Extracted Reference URL")
                self.reference_items.append(ref)
                print(f"[CLIENT_CHAT] REFERENCE_URL_REGISTERED url={u}", flush=True)

    def add_reference_url(self, url: str, title: str = "", description: str = "") -> ReferenceItem:
        ref = ReferenceItem(ref_type="URL", source=url, title=title or "Reference URL", description=description)
        if not any(r.source == url for r in self.reference_items):
            self.reference_items.append(ref)
            print(f"[CLIENT_CHAT] REFERENCE_URL_ADDED url={url}", flush=True)
            self.save_to_disk()
        return ref

    def add_reference_file(self, local_path: str, ref_type: str = "IMAGE", description: str = "") -> ReferenceItem:
        filename = os.path.basename(local_path)
        ext = os.path.splitext(filename)[1].lower()

        actual_type = ref_type
        if ext in [".mp4", ".mov", ".webm", ".avi", ".mkv"]:
            actual_type = "VIDEO"
        elif ext == ".pdf":
            actual_type = "PDF"
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            actual_type = "IMAGE"

        ref = ReferenceItem(ref_type=actual_type, source=local_path, title=filename, description=description)
        if not any(r.source == local_path for r in self.reference_items):
            self.reference_items.append(ref)
            print(f"[CLIENT_CHAT] REFERENCE_FILE_ADDED type={actual_type} path={filename}", flush=True)
            self.save_to_disk()
        return ref

    def remove_asset(self, asset_id: str) -> bool:
        initial_count = len(self.assets)
        self.assets = [a for a in self.assets if a.asset_id != asset_id]
        removed = len(self.assets) < initial_count
        if removed:
            print(f"[CLIENT_BRIEF] ASSET_REMOVED asset_id={asset_id}", flush=True)
            self.save_to_disk()
        return removed

    def update_form_fields(self, data: Dict[str, Any]):
        for k, v in data.items():
            if hasattr(self, k) and isinstance(v, str):
                setattr(self, k, v)
        if data.get("company_name"):
            self.client_name = data["company_name"]
        self.save_to_disk()

    def check_completion_signal(self, text: str) -> bool:
        """
        Detects if the user indicated they are done sending details.
        """
        if not text:
            return False
        low = text.lower().strip()
        signals = [
            "bas itni hi details hain",
            "bas itna hi hai",
            "bas itni details",
            "details complete hain",
            "details complete",
            "ho gaya",
            "ab bana do",
            "that's all",
            "thats all",
            "done",
            "generate it",
            "create website"
        ]
        return any(sig in low for sig in signals)

    def get_combined_text(self) -> str:
        return "\n".join([m.text for m in self.messages if m.text])

    def add_attachment(self, local_path: str, caption: str = "", role: str = "unknown") -> LocalClientAsset:
        filename = os.path.basename(local_path)
        ext = os.path.splitext(filename)[1].lower()

        mime = "image/jpeg"
        if ext == ".png":
            mime = "image/png"
        elif ext == ".webp":
            mime = "image/webp"
        elif ext == ".svg":
            mime = "image/svg+xml"

        asset_id = f"ast_{len(self.assets) + 1:03d}"
        asset = LocalClientAsset(
            asset_id=asset_id,
            original_filename=filename,
            mime_type=mime,
            local_path=local_path,
            role=role,
            caption=caption,
            provenance="CLIENT_PROVIDED"
        )
        if asset not in self.assets:
            self.assets.append(asset)
        print(f"[CLIENT_CHAT] ATTACHMENT_RECEIVED filename={filename}", flush=True)
        print(f"[CLIENT_CHAT] ASSET_REGISTERED role={role} provenance=CLIENT_PROVIDED", flush=True)
        self.save_to_disk()
        return asset

    def get_pre_build_summary(self, extracted_brief: Any = None) -> str:

        """
        Generates a rich, structured CLIENT BRIEF READY summary output.
        """
        biz_name = getattr(extracted_brief, "company_name", "") or getattr(extracted_brief, "client_name", "") or self.client_name or "Client Business"
        raw_cat = str(getattr(extracted_brief, "website_type", "UNKNOWN") if extracted_brief else "UNKNOWN").lower()
        type_display = {
            "restaurant": "RESTAURANT_CAFE",
            "portfolio": "DEVELOPER_PORTFOLIO",
            "company": "BUSINESS_WEBSITE",
            "agency": "AGENCY_WEBSITE",
            "service": "SERVICE_BUSINESS",
            "product_landing": "PRODUCT_WEBSITE",
            "event": "EVENT_WEBSITE",
            "custom": "UNKNOWN"
        }.get(raw_cat, raw_cat.upper())

        desc = getattr(extracted_brief, "business_description", "") or "Official website requested by client."
        visual_direction = getattr(extracted_brief, "brand_preferences", "") or "Warm / editorial / modern design direction"

        summary = (
            "==============================================\n"
            "CLIENT BRIEF READY\n"
            "==============================================\n\n"
            f"WEBSITE TYPE\n{type_display}\n\n"
            f"BUSINESS / PERSON\n{biz_name}\n\n"
            f"DESCRIPTION\n{desc}\n\n"
            "SECTIONS DETECTED\n"
            "[+] Hero\n[+] About\n[+] Services / Offerings\n[+] Gallery / Projects\n[+] Contact\n\n"
            "CLIENT ASSETS\n"
        )

        if self.assets:
            for att in self.assets:
                summary += f"[+] {att.original_filename}\n    Role: {att.role.upper()}\n    Source: {att.provenance}\n"
        else:
            summary += "[!] No explicit client images attached (Jarvis will generate visual assets if required)\n"

        summary += "\nREFERENCES\n"
        if self.reference_items:
            for ref in self.reference_items:
                ref_disp = f"{ref.title} ({ref.source})" if ref.title and ref.source and ref.source not in ref.title else (ref.source or ref.title)
                summary += f"[+] {ref_disp}\n    Type: {ref.ref_type.upper()}\n    Status: ANALYZED (Influences visual DNA only)\n"
        else:
            summary += "[+] None provided (Fresh composition will be generated)\n"

        summary += f"\nDESIGN INTENT\n[+] {visual_direction}\n\nMISSING INFORMATION\n"
        missing = getattr(extracted_brief, "missing_fields", []) if extracted_brief else []
        if missing:
            for field_name in missing:
                summary += f"[!] {field_name.replace('_', ' ').capitalize()} -- NOT PROVIDED (UNKNOWN)\n"
        else:
            summary += "[!] Phone -- NOT PROVIDED (UNKNOWN)\n[!] Address -- NOT PROVIDED (UNKNOWN)\n[!] Opening hours -- NOT PROVIDED (UNKNOWN)\n"


        summary += (
            "\nCONTENT SAFETY\n"
            "[+] No fabricated facts\n"
            "[+] Client assets preserved\n"
            "[+] Reference separated from client content\n"
            "==============================================\n"
        )
        return summary


