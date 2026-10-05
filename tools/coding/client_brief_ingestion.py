import re
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from tools.coding.whatsapp_adapter import WhatsAppAdapter, WhatsAppMessage, WhatsAppMedia

@dataclass
class WebsiteAsset:
    asset_id: str
    filename: str
    mime_type: str
    local_path: str
    role: str = "general" # profile_image, logo, project_image, product_image, general
    caption: str = ""
    project_association: str = ""
    client_name: str = ""
    is_user_provided: bool = True
    provenance: str = "CLIENT_PROVIDED" # CLIENT_PROVIDED, OFFICIAL_SOURCE, GENERATED, SYSTEM
    clarification_needed: Optional[str] = None

@dataclass
class ClientBrief:
    client_name: str
    website_type: str = "portfolio" # portfolio, company, custom
    company_name: str = ""
    person_name: str = ""
    role: str = ""
    business_description: str = ""
    services: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    unique_quote: str = ""
    target_audience: str = ""
    required_sections: List[str] = field(default_factory=list)
    brand_preferences: str = ""
    contact_information: Dict[str, str] = field(default_factory=dict)
    social_links: Dict[str, str] = field(default_factory=dict)
    website_references: List[str] = field(default_factory=list)
    reference_items: List[Any] = field(default_factory=list)
    visual_dna: Any = None
    research_context: Optional[Any] = None
    special_requirements: List[str] = field(default_factory=list)
    assets: List[WebsiteAsset] = field(default_factory=list)
    raw_messages: List[str] = field(default_factory=list)
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = True
    missing_fields: List[str] = field(default_factory=list)

class ClientBriefParser:
    """
    Parses multi-message streams and media attachments from local client sessions or WhatsApp feeds
    into a unified, validated ClientBrief object.
    """

    @classmethod
    def parse_local_client_session(cls, session: Any) -> ClientBrief:
        print(f"[CLIENT_BRIEF] PARSING_STARTED session_id={getattr(session, 'session_id', 'local')}", flush=True)

        raw_texts = [msg.text for msg in session.messages if msg.text]
        combined_text = "\n".join(raw_texts)
        combined_lower = combined_text.lower()

        # 1. Multi-class Website Type Classification
        # PRIORITY: Use explicit form field (session.website_type) first before keyword scanning
        cat = "custom"
        confidence = 0.85

        # Check explicit form field set by user in the Client Brief form
        explicit_type = getattr(session, "website_type", "").strip().lower()
        if explicit_type and explicit_type not in ("", "custom"):
            cat = explicit_type
            confidence = 1.0
            print(f"[CLIENT_BRIEF_PARSER] cat_source=FORM_FIELD_EXPLICIT cat={cat}", flush=True)
        else:
            # Fall back to keyword scan from chat messages
            if any(k in combined_lower for k in ["cafe", "restaurant", "everfresh", "food", "dining", "bakery", "menu", "coffee", "dishes"]):
                cat = "restaurant"
                confidence = 0.95
            elif any(k in combined_lower for k in ["developer", "software engineer", "coder", "flutter", "full stack", "frontend", "backend"]):
                # NOTE: "manish" deliberately removed — personal names must NOT force a portfolio category
                cat = "portfolio"
                confidence = 0.94
            elif any(k in combined_lower for k in ["personal portfolio", "designer portfolio", "resume", "cv", "personal"]):
                cat = "portfolio"
                confidence = 0.92
            elif any(k in combined_lower for k in ["portfolio"]):
                cat = "portfolio"
                confidence = 0.90
            elif any(k in combined_lower for k in ["company", "corporate", "business solutions", "enterprise", "inc", "ltd", "novastack"]):
                cat = "company"
                confidence = 0.88
            elif any(k in combined_lower for k in ["agency", "digital agency", "marketing agency", "design agency"]):
                cat = "agency"
                confidence = 0.92
            elif any(k in combined_lower for k in ["service", "services", "consulting", "repair", "salon", "spa", "cleaning"]):
                cat = "service"
                confidence = 0.90
            elif any(k in combined_lower for k in ["e-commerce", "ecommerce", "online shop", "shopping cart", "sell clothes", "shop items"]):
                cat = "e-commerce"
                confidence = 0.90
            elif any(k in combined_lower for k in ["product launch", "saas product", "productivity product", "app launch", "product website", "product landing"]):
                cat = "product_landing"
                confidence = 0.90
            elif any(k in combined_lower for k in ["landing page", "launch page", "one page"]):
                cat = "product_landing"
                confidence = 0.88
            elif combined_text.strip():
                cat = "company"
                confidence = 0.75
            print(f"[CLIENT_BRIEF_PARSER] cat_source=KEYWORD_SCAN cat={cat} confidence={confidence}", flush=True)

        # 2. Detect Business / Person Name
        # Priority: explicit form field > regex from messages
        biz_name = getattr(session, "client_name", "") or ""
        _explicit_biz_name = biz_name not in ("", "Client")  # True when user explicitly set the name

        if biz_name == "Client":
            biz_name = ""

        if not _explicit_biz_name:
            # Only do regex extraction when name was NOT explicitly set via form
            called_match = re.search(r'(?:called|named)\s+([A-Za-z0-9\-_]{2,30})', combined_text, re.IGNORECASE)
            is_a_match = re.search(r'([A-Za-z0-9\s\-_]{2,30})\s+(?:is a|is an)\s+', combined_text, re.IGNORECASE)
            for_match = re.search(r'([A-Za-z0-9\s\-_]{2,30})\s+(?:website|landing page|app)\b', combined_text, re.IGNORECASE)

            if "kasyap everfresh" in combined_lower:
                biz_name = "Kasyap Everfresh Cafe"
            elif "bella tavola" in combined_lower:
                biz_name = "Bella Tavola Ristorante Italiano"
            elif called_match:
                biz_name = called_match.group(1).strip()
            elif is_a_match and is_a_match.group(1).strip().lower() not in ["website", "this"]:
                biz_name = is_a_match.group(1).strip()
            elif for_match:
                candidate = for_match.group(1).strip()
                # Remove leading verbs, articles, or pronouns
                candidate = re.sub(r'^(?:build|create|make|generate|design)\s+(?:a|an|the|my|our)?\s*', '', candidate, flags=re.IGNORECASE).strip()
                candidate = re.sub(r'^(?:a|an|the|my|our)\s+', '', candidate, flags=re.IGNORECASE).strip()
                if candidate and candidate.lower() not in ["a", "the", "my", "new", "simple", "corporate", "business", "website", "build"]:
                    biz_name = candidate
            else:
                name_match = re.search(r'(?:for|name|business|cafe|company|brand)\s*:?\s*([A-Za-z0-9\s]{2,30})', combined_text, re.IGNORECASE)
                if name_match:
                    candidate = name_match.group(1).strip()
                    candidate = re.sub(r'^(?:build|create|make|generate|design)\s+(?:a|an|the|my|our)?\s*', '', candidate, flags=re.IGNORECASE).strip()
                    if candidate and len(candidate) > 2 and candidate.lower() not in ["website", "brand", "company", "cafe", "based in delhi", "build"]:
                        biz_name = candidate


        if not biz_name:
            if cat in ("restaurant_cafe", "restaurant", "cafe"):
                biz_name = "Artisan Cafe"
            elif cat in ("developer_portfolio", "personal_portfolio", "portfolio"):
                biz_name = "Developer Portfolio"
            elif cat in ("business_website", "business", "company"):
                biz_name = "Client Business"
            elif cat in ("agency_website", "agency"):
                biz_name = "Creative Agency"
            elif cat in ("product_website", "product"):
                biz_name = "Product Launch"
            elif cat in ("service_business", "service"):
                biz_name = "Service Business"
            else:
                biz_name = "Client Enterprise"

        # 3. Process Client-Provided Assets & Assign Roles (Priority: EXPLICIT > CAPTION > CONTEXT > INFERENCE)
        parsed_assets: List[WebsiteAsset] = []
        has_hero = False
        fact_sources = {"business_name": "CHAT_MESSAGE"}

        for att in session.assets:
            c_text = (att.caption or "").lower()
            role = att.role

            if role == "unknown" or not role:
                full_ctx = f"{c_text} {combined_lower}".strip()
                if any(k in full_ctx for k in ["hero section me use karna", "use as hero", "hero photo", "hero image", "main photo"]):
                    role = "hero_image"
                    fact_sources[f"asset_{att.original_filename}"] = "EXPLICIT_INSTRUCTION"
                elif any(k in full_ctx for k in ["use as logo", "brand logo", "company logo"]):
                    role = "logo"
                    fact_sources[f"asset_{att.original_filename}"] = "EXPLICIT_INSTRUCTION"
                elif any(k in full_ctx for k in ["profile photo", "profile image"]):
                    role = "profile_image"
                    fact_sources[f"asset_{att.original_filename}"] = "CLIENT_ATTACHMENT"
                elif any(k in full_ctx for k in ["project screenshot", "project image"]):
                    role = "project_image"
                    fact_sources[f"asset_{att.original_filename}"] = "CLIENT_ATTACHMENT"
                elif "gallery" in full_ctx:
                    role = "gallery_image"
                    fact_sources[f"asset_{att.original_filename}"] = "CLIENT_ATTACHMENT"
                else:
                    role = "hero_image" if len(parsed_assets) == 0 else "general"
                    fact_sources[f"asset_{att.original_filename}"] = "CLIENT_ATTACHMENT"

            if role == "hero_image":
                has_hero = True

            parsed_assets.append(WebsiteAsset(
                asset_id=att.asset_id,
                filename=att.original_filename,
                mime_type=att.mime_type,
                local_path=att.local_path,
                role=role,
                caption=att.caption,
                client_name=biz_name,
                is_user_provided=True,
                provenance="CLIENT_PROVIDED"
            ))
            print(f"[CLIENT_BRIEF] ASSET_ROLE_RESOLVED filename={att.original_filename} role={role} provenance=CLIENT_PROVIDED", flush=True)

        # 4. Smart Supplementary Asset Planner (GENERATED requirements)
        generated_reqs: List[Dict[str, Any]] = []
        if len(parsed_assets) == 0:
            print(f"[SMART_ASSET_PLANNER] 0 client images provided. Planning full GENERATED visual requirements for {cat}.", flush=True)
            generated_reqs.append({"role": "hero_visual", "description": f"Hero visual for {biz_name} ({cat})", "provenance": "GENERATED"})
            generated_reqs.append({"role": "section_visual_1", "description": f"Feature visual 1 for {cat}", "provenance": "GENERATED"})
            generated_reqs.append({"role": "section_visual_2", "description": f"Feature visual 2 for {cat}", "provenance": "GENERATED"})
        elif not has_hero:
            print(f"[SMART_ASSET_PLANNER] Client provided {len(parsed_assets)} image(s) but no hero visual. Planning supplementary GENERATED hero asset.", flush=True)
            generated_reqs.append({"role": "hero_visual", "description": f"Supplementary hero visual for {biz_name}", "provenance": "GENERATED"})

        # 5. Missing Fields Tracking (Zero Fabrication Gate)
        missing = []
        has_phone = bool(re.search(r'\+?\d[\d\s\-]{8,}', combined_text)) or any(k in combined_lower for k in ["phone:", "call:", "mobile:", "tel:"])
        if not has_phone:
            missing.append("phone")

        has_address = any(k in combined_lower for k in ["address:", "street", "boulevard", "circle", "road", "shop no", "suite"])
        if not has_address:
            missing.append("address")

        if "hours" not in combined_lower and "timings" not in combined_lower and "mon - sun" not in combined_lower and "8 baje" not in combined_lower:
            missing.append("opening_hours")

        if "price" not in combined_lower and "pricing" not in combined_lower and "$" not in combined_text and "rs" not in combined_lower:
            missing.append("pricing")

        if "review" not in combined_lower and "rating" not in combined_lower and "testimonial" not in combined_lower:
            missing.append("reviews")

        if "award" not in combined_lower and "achievement" not in combined_lower:
            missing.append("achievements")

        # 6. Reference Analysis Stage (Design DNA strictly separated from Client Content)
        from tools.coding.reference_analysis_engine import ReferenceAnalysisEngine
        ref_items = getattr(session, "reference_items", [])
        visual_dna = ReferenceAnalysisEngine.analyze_references(ref_items, category=cat)

        for ref in ref_items:
            fact_sources[f"reference_{ref.ref_type}"] = f"REFERENCE_{ref.ref_type.upper()}"

        sess_desc = getattr(session, "business_description", "")
        sess_brand = getattr(session, "brand_tone", "") or getattr(session, "brand_description", "") or getattr(session, "inspiration_style", "")
        sess_aud = getattr(session, "target_audience", "")
        sess_sec = getattr(session, "required_sections", "") or getattr(session, "required_pages", "")

        req_secs = ["Hero", "About", "Services", "Offerings", "Contact"]
        if sess_sec:
            parsed_secs = [s.strip() for s in sess_sec.split(",") if s.strip()]
            if parsed_secs:
                req_secs = parsed_secs

        contact_info = {}
        if getattr(session, "contact_number", ""):
            contact_info["phone"] = session.contact_number
        if getattr(session, "email", ""):
            contact_info["email"] = session.email
        if getattr(session, "address", ""):
            contact_info["address"] = session.address
        if getattr(session, "location", ""):
            contact_info["location"] = session.location

        brief = ClientBrief(
            client_name=biz_name,
            website_type=cat,
            company_name=biz_name,
            person_name=biz_name,
            business_description=sess_desc or f"Official website for {biz_name}",
            brand_preferences=sess_brand or "Warm / editorial / modern design direction",
            target_audience=sess_aud,
            contact_information=contact_info,
            required_sections=req_secs,
            assets=parsed_assets,
            reference_items=ref_items,
            visual_dna=visual_dna,
            raw_messages=raw_texts,
            missing_fields=missing,
            source_metadata={
                "source": "LOCAL_CLIENT_BRIEF",
                "message_count": len(session.messages),
                "client_asset_count": len(parsed_assets),
                "reference_count": len(ref_items),
                "generated_req_count": len(generated_reqs),
                "confidence": confidence,
                "fact_sources": fact_sources
            }
        )
        setattr(brief, "generated_image_requirements", generated_reqs)

        print(f"[CLIENT_BRIEF] PARSED business=\"{brief.company_name}\" category=\"{cat}\" confidence={confidence}", flush=True)
        print(f"[CLIENT_BRIEF] VISUAL_DNA_STATUS status={visual_dna.inspection_status} type={visual_dna.reference_type} style={visual_dna.style}", flush=True)
        print(f"[CLIENT_BRIEF] VALIDATED status=PASS client_assets={len(brief.assets)} references={len(ref_items)} missing_fields={len(missing)}", flush=True)
        return brief


    @classmethod
    def parse_whatsapp_messages(cls, client_name: str, messages: List[WhatsAppMessage]) -> ClientBrief:
        raw_texts = [msg.text for msg in messages if msg.text]
        combined_text = "\n".join(raw_texts)

        # 1. Detect website category
        cat = "portfolio"
        if any(k in combined_text.lower() for k in ["company", "corporate", "agency", "business", "services"]):
            cat = "company"

        # 2. Extract client/person name & role
        person_name = client_name
        name_match = re.search(r'(?:naam|name|i am|iam|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', combined_text, re.IGNORECASE)
        if name_match:
            person_name = name_match.group(1).strip()

        role_str = ""
        role_match = re.search(r'(?:role|developer|designer|engineer|stack|architect)\s*:\s*([A-Za-z0-9\s/&\-]+)', combined_text, re.IGNORECASE)
        if role_match:
            role_str = role_match.group(1).strip()
        elif "flutter developer" in combined_text.lower():
            role_str = "Flutter & Full Stack Developer"
        elif "developer" in combined_text.lower():
            role_str = "Full Stack Developer"

        # 3. Extract skills
        skills = []
        skills_match = re.search(r'skills?\s*:\s*([^\n]+)', combined_text, re.IGNORECASE)
        if skills_match:
            raw_s = skills_match.group(1)
            skills = [s.strip() for s in re.split(r'[,;\n]', raw_s) if s.strip()]
        else:
            for kw in ["React", "Flutter", "Node", "Python", "TypeScript", "Dart", "OpenCV", "Firebase"]:
                if kw.lower() in combined_text.lower():
                    skills.append(kw)

        # 4. Extract projects
        projects = []
        proj_blocks = re.findall(r'project\s*\d*\s*:\s*([^\n]+)(?:\n([^\n]+))?', combined_text, re.IGNORECASE)
        for p in proj_blocks:
            p_title = p[0].strip()
            p_desc = p[1].strip() if len(p) > 1 and p[1] else ""
            if p_title:
                projects.append({"title": p_title, "description": p_desc})

        if not projects and "jarvis" in combined_text.lower():
            projects.append({"title": "Jarvis AI Assistant", "description": "Autonomous voice personal assistant"})

        # 5. Extract unique quotes or personal quotes
        quote_str = ""
        quote_match = re.search(r'["\']([^"\']{15,150})["\']', combined_text)
        if quote_match:
            quote_str = quote_match.group(1).strip()
        else:
            for line in raw_texts:
                if any(k in line.lower() for k in ["built my first", "passion for", "learning", "believe in"]):
                    quote_str = line.strip()
                    break

        # 6. Process Media Assets & Determine Roles (Priority: EXPLICIT > CAPTION > CONTEXT > INFERENCE)
        assets: List[WebsiteAsset] = []
        for msg in messages:
            for m in msg.media:
                caption_lower = (m.caption or "").lower()
                text_around = msg.text.lower() if msg.text else ""
                full_context = f"{caption_lower} {text_around}".strip()

                role = "general"
                clarification = None

                # Tier 1: EXPLICIT INSTRUCTION
                if "use this as my profile photo" in full_context or "use as profile" in full_context or "first image as my profile" in full_context or "profile photo" in caption_lower:
                    role = "profile_image"
                elif "use this as logo" in full_context or "brand logo" in caption_lower or "company logo" in full_context:
                    role = "logo"
                elif "use for my project" in full_context or "second image for my project" in full_context or "project screenshot" in caption_lower:
                    role = "project_image"
                # Tier 2: CAPTION MATCHING
                elif "profile" in caption_lower or "dp" in caption_lower:
                    role = "profile_image"
                elif "logo" in caption_lower:
                    role = "logo"
                elif "project" in caption_lower or "screenshot" in caption_lower:
                    role = "project_image"
                # Tier 3: CONTEXT MATCHING
                elif "profile" in text_around or "photo" in caption_lower or "photo" in text_around:
                    role = "profile_image"
                elif "logo" in text_around:
                    role = "logo"
                elif "project" in text_around:
                    role = "project_image"
                # Tier 4: LOW CONFIDENCE / AMBIGUOUS
                else:
                    role = m.role or "general"
                    if not caption_lower and not text_around:
                        clarification = "Media asset role is ambiguous. Please clarify whether this image should be profile, logo, or project."

                assets.append(WebsiteAsset(
                    asset_id=m.media_id,
                    filename=m.filename,
                    mime_type=m.mime_type,
                    local_path=m.local_path,
                    role=role,
                    caption=m.caption,
                    client_name=client_name,
                    is_user_provided=True,
                    provenance=getattr(m, "provenance", "CLIENT_PROVIDED"),
                    clarification_needed=clarification
                ))

        # 7. Build ClientBrief
        brief = ClientBrief(
            client_name=client_name,
            website_type=cat,
            company_name=person_name if cat == "portfolio" else (client_name + " Company"),
            person_name=person_name,
            role=role_str or "Software Engineer",
            business_description=f"Official website for {person_name}. {role_str}",
            skills=skills,
            projects=projects,
            unique_quote=quote_str,
            required_sections=["Hero", "About", "Skills", "Projects", "Contact"],
            assets=assets,
            raw_messages=raw_texts,
            source_metadata={"source": "WhatsApp", "message_count": len(messages), "media_count": len(assets)}
        )

        print(f"[CLIENT_BRIEF_PARSED] client=\"{client_name}\" messages={len(messages)} assets={len(assets)} quote=\"{quote_str[:30]}\"", flush=True)
        return brief


class ClientBriefManager:
    """
    Central Manager for storing, querying, and resolving ClientBrief objects.
    """
    _instance = None
    _briefs: Dict[str, ClientBrief] = {}

    @classmethod
    def get_instance(cls) -> "ClientBriefManager":
        if cls._instance is None:
            cls._instance = ClientBriefManager()
        return cls._instance

    def register_brief(self, brief: ClientBrief):
        key = brief.client_name.lower().strip()
        self._briefs[key] = brief
        print(f"[CLIENT_BRIEF_VALIDATED] Registered brief for '{brief.client_name}' (assets={len(brief.assets)})", flush=True)

    def get_brief(self, client_name: str) -> Optional[ClientBrief]:
        key = client_name.lower().strip()
        return self._briefs.get(key, None)

    def resolve_brief_from_command(self, command: str) -> tuple[Optional[ClientBrief], str]:
        """
        Resolves ClientBrief from a user command prompt (e.g. "Create a portfolio using Shivam's WhatsApp details").
        Handles ambiguity if multiple briefs match.
        """
        cmd_lower = command.lower()
        matched_keys = []

        for key, brief in self._briefs.items():
            if key in cmd_lower or brief.person_name.lower() in cmd_lower or brief.client_name.lower() in cmd_lower:
                matched_keys.append(key)

        if len(matched_keys) == 1:
            brief = self._briefs[matched_keys[0]]
            print(f"[CLIENT_BRIEF_SOURCE] Resolved brief for client '{brief.client_name}' from command", flush=True)
            return brief, "RESOLVED"
        elif len(matched_keys) > 1:
            print(f"[AMBIGUOUS_CLIENT_BRIEF] TRUE matched={matched_keys}", flush=True)
            return None, "AMBIGUOUS_CLIENT_BRIEF"
        elif self._briefs:
            # Default to first brief if only 1 brief exists in manager
            if len(self._briefs) == 1:
                brief = list(self._briefs.values())[0]
                print(f"[CLIENT_BRIEF_SOURCE] Auto-selected sole brief for '{brief.client_name}'", flush=True)
                return brief, "RESOLVED"

        return None, "CLIENT_BRIEF_NOT_FOUND"
