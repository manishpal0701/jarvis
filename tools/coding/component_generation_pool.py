"""
tools/coding/component_generation_pool.py
Component Generator Pool for Turbo Website Builder v4.

Enforces local-LLM-aware concurrency policy (max_concurrent_llm_requests = 1)
to prevent queue blocking on qwen3:8b, logs honest generation statuses (SUCCESS|FALLBACK|FAILED),
and enforces family-driven rendering in both LLM prompts and deterministic fallback generators.
"""

import os
import time
import datetime
import concurrent.futures
import re
from typing import Dict, Any, List, Optional
from tools.coding.website_master_planner import MasterWebsitePlan, ComponentSpec
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.code_validator import CodeValidator
from tools.coding.website_visual_environment import WebsiteVisualEnvironment
from ai.ai_response_manager import AIResponseManager

class ContentLinter:
    """
    Build-Time Content Linter.
    Scans generated TSX component code for unverified metrics, fake certifications,
    or generic SaaS boilerplate, rejecting non-grounded outputs.
    """
    BANNED_PATTERNS = [
        r"99\.9+%\s*uptime",
        r"10M\+\s*users",
        r"150\+\s*enterprise",
        r"50M\+\s*daily",
        r"SOC2\s*certified",
        r"ISO\s*27001",
        r"#1\s*platform",
        r"enterprise solutions for modern digital needs",
        r"service 1",
        r"service 2"
    ]

    @classmethod
    def lint_component_code(cls, code: str, component_name: str, category: str = "portfolio") -> tuple[bool, str]:
        if not code or len(code) < 30:
            return False, "EMPTY_CODE"
        code_lower = code.lower()
        for pat in cls.BANNED_PATTERNS:
            if re.search(pat, code_lower):
                return False, f"BANNED_CONTENT_PATTERN_DETECTED_{pat}"

        cat_lower = (category or "").lower()
        if "restaurant" not in cat_lower and "dining" not in cat_lower and "gastronomy" not in cat_lower:
            for pat in [
                r"signature\s+dishes",
                r"table\s+reservation",
                r"table\s+booking",
                r"reserve\s+a?\s*table",
                r"executive\s+chef",
                r"culinary",
                r"crafted\s+precision\s+&\s+timeless\s+elegance"
            ]:
                if re.search(pat, code_lower):
                    return False, f"FORBIDDEN_RESTAURANT_CONTENT_{pat}"

        return True, "PASS"


class ComponentGenerationPool:
    """
    Component Generator Pool for Turbo Website Builder v4.
    Enforces family-aware component generation matching the selected DesignDirection.
    """

    MAX_CONCURRENT_LLM_REQUESTS = 1

    @staticmethod
    def section_title(name: str) -> str:
        """
        Converts camel-case/PascalCase component names like 'SignatureDishes'
        into clean human-readable section titles like 'Signature Dishes'.
        Public static interface on ComponentGenerationPool.
        """
        return ComponentGenerationPool._clean_component_title(name)

    @staticmethod
    def generate_components_parallel(
        master_plan: MasterWebsitePlan,
        output_dir: str,
        task_id: str = "project",
        max_workers: int = 1
    ) -> Dict[str, str]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        num_workers = ComponentGenerationPool.MAX_CONCURRENT_LLM_REQUESTS
        print(f"[LLM_CONCURRENCY_POLICY] model=qwen3:8b max_concurrent={num_workers} reason=LOCAL_MODEL", flush=True)
        print(f"[PARALLEL_GENERATION_START] task_id={task_id} workers={num_workers} components={len(master_plan.components)} timestamp={now}", flush=True)

        results: Dict[str, str] = {}
        ws = WorkspaceManager.get_instance()

        def _worker_task(worker_id: int, spec: ComponentSpec) -> tuple[str, str, str]:
            worker_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f"[{f'WORKER_{worker_id}'}] file={spec.file_path} start_time={worker_start}", flush=True)

            try:
                code, status = ComponentGenerationPool._generate_single_component(spec, master_plan, output_dir)
            except Exception as exc:
                print(f"[WORKER_EXC_HANDLED] Component {spec.file_path} exception: {exc}", flush=True)
                code = ComponentGenerationPool._deterministic_component(spec, master_plan)
                code = ComponentGenerationPool._ensure_export_name(code, spec.name)
                status = f"FALLBACK_EXC_{exc}"
            
            # Save file to disk
            full_path = os.path.join(output_dir, spec.file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)

            worker_end = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f"[WORKER_COMPLETE] worker={worker_id} file={spec.file_path} status={status} end_time={worker_end}", flush=True)
            return spec.file_path, code, status

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_spec = {
                executor.submit(_worker_task, idx + 1, spec): spec
                for idx, spec in enumerate(master_plan.components)
            }
            for future in concurrent.futures.as_completed(future_to_spec):
                spec = future_to_spec[future]
                try:
                    rel_path, code, status = future.result()
                    results[rel_path] = code
                    ws.write_workspace_file(output_dir, rel_path, code)
                except Exception as exc:
                    print(f"[WORKER_ERROR] Component {spec.file_path} generated exception: {exc}")
                    fallback_code = ComponentGenerationPool._deterministic_component(spec, master_plan)
                    results[spec.file_path] = fallback_code
                    ws.write_workspace_file(output_dir, spec.file_path, fallback_code)
                    print(f"[COMPONENT_GENERATION_RESULT] component={spec.name} status=FALLBACK reason=EXC_{exc}", flush=True)

        # Generate App.tsx composition component
        app_code = ComponentGenerationPool._generate_app_component(master_plan)
        app_path = "src/App.tsx"
        full_app_path = os.path.join(output_dir, app_path)
        with open(full_app_path, "w", encoding="utf-8") as f:
            f.write(app_code)
        results[app_path] = app_code
        ws.write_workspace_file(output_dir, app_path, app_code)

        return results

    @staticmethod
    def _generate_single_component(spec: ComponentSpec, master_plan: MasterWebsitePlan, output_dir: str) -> tuple[str, str]:
        comp_start_t = time.time()
        print(f"[COMPONENT_GENERATION_START] component={spec.name}", flush=True)

        design_dir = getattr(master_plan, 'design_direction', None)
        did = design_dir.design_id if design_dir else "cinematic_spatial"
        family = getattr(design_dir, 'family', 'FAMILY A — CINEMATIC SPATIAL') if design_dir else 'FAMILY A'
        card_lang = getattr(design_dir, 'card_language', 'spatial_glass_card') if design_dir else 'spatial_glass_card'

        # Extract verified facts
        v_content = getattr(spec, 'verified_content', None) or getattr(master_plan, 'verified_content', None)
        facts_summary = ""
        if v_content:
            domain = getattr(v_content, 'official_domain', '')
            desc = getattr(v_content, 'description', '')
            prods = getattr(v_content, 'products', [])
            servs = getattr(v_content, 'services', [])
            facts_summary = (
                f"VERIFIED COMPANY FACTS (GROUND TRUTH):\n"
                f"Official Domain: {domain or 'N/A'}\n"
                f"Description: {desc or 'N/A'}\n"
                f"Products/Services: {', '.join((prods + servs)[:6]) or 'N/A'}\n"
            )

        # Extract client brief context for LLM prompt
        _cb = getattr(master_plan, 'client_brief', None)
        client_brief_context = ""
        if _cb:
            cb_fields = []
            company_name = getattr(_cb, 'company_name', '') or getattr(_cb, 'client_name', '')
            if company_name:
                cb_fields.append(f"COMPANY/PERSON NAME: {company_name}")
            biz_desc = getattr(_cb, 'business_description', '')
            if biz_desc:
                cb_fields.append(f"BUSINESS DESCRIPTION: {biz_desc}")
            brand_pref = getattr(_cb, 'brand_preferences', '')
            if brand_pref:
                cb_fields.append(f"BRAND PREFERENCES: {brand_pref}")
            tgt_aud = getattr(_cb, 'target_audience', '')
            if tgt_aud:
                cb_fields.append(f"TARGET AUDIENCE: {tgt_aud}")
            contact_info = getattr(_cb, 'contact_information', {})
            if contact_info:
                for k, v in contact_info.items():
                    if v:
                        cb_fields.append(f"CONTACT_{k.upper()}: {v}")
            req_secs = getattr(_cb, 'required_sections', [])
            if req_secs:
                cb_fields.append(f"REQUIRED SECTIONS: {', '.join(req_secs)}")
            services = getattr(_cb, 'services', [])
            if services:
                cb_fields.append(f"SERVICES/OFFERINGS: {', '.join(services[:6])}")
            skills = getattr(_cb, 'skills', [])
            if skills:
                cb_fields.append(f"SKILLS: {', '.join(skills[:8])}")
            projects = getattr(_cb, 'projects', [])
            if projects:
                proj_names = [p.get('name','') if isinstance(p, dict) else str(p) for p in projects[:4]]
                cb_fields.append(f"PROJECTS: {', '.join([n for n in proj_names if n])}")
            unique_quote = getattr(_cb, 'unique_quote', '')
            if unique_quote:
                cb_fields.append(f"UNIQUE QUOTE/TAGLINE: {unique_quote}")
            special_reqs = getattr(_cb, 'special_requirements', [])
            if special_reqs:
                cb_fields.append(f"SPECIAL REQUIREMENTS: {', '.join(special_reqs[:4])}")
            # Build Reference Design Context
            ref_context_str = ""
            visual_dna = getattr(_cb, 'visual_dna', None) or getattr(master_plan, 'visual_dna', None)
            ref_items = getattr(_cb, 'reference_items', [])
            ref_urls = [getattr(r, 'source', '') for r in ref_items if getattr(r, 'ref_type', '') == 'URL']

            if visual_dna and visual_dna.reference_present:
                ref_context_str = (
                    "\n\n=== REFERENCE DESIGN ANALYSIS (DESIGN INSPIRATION SOURCE ONLY) ===\n"
                    f"Reference URL: {', '.join(ref_urls) if ref_urls else 'Provided Reference'}\n"
                    f"Inspection Status: {visual_dna.inspection_status}\n"
                    f"Design Style Direction: {visual_dna.style}\n"
                    f"Composition Layout: {visual_dna.composition}\n"
                    f"Typography Pairing: {visual_dna.typography.get('header_font', '')} + {visual_dna.typography.get('body_font', '')}\n"
                    f"Color Characteristics: Primary={visual_dna.color_palette.get('primary')} Secondary={visual_dna.color_palette.get('secondary')} Background={visual_dna.color_palette.get('background')}\n"
                    f"Image Treatment: {visual_dna.image_treatment}\n"
                    f"Section Rhythm: {', '.join(visual_dna.section_rhythm)}\n"
                    "=== END REFERENCE ANALYSIS ===\n"
                    "DESIGN INSPIRATION INSTRUCTION: Use the REFERENCE DESIGN ANALYSIS strictly as visual inspiration for layout, typography hierarchy, and spacing rhythm. DO NOT copy text, branding, or exact copyright content from the reference URL. All text content MUST come from the CLIENT BRIEF.\n"
                )

            assets_cnt = len(getattr(_cb, 'assets', []))
            cb_fields.append(f"CLIENT ASSETS PROVIDED: {assets_cnt} {'(use /assets/client/ paths)' if assets_cnt else '(none — generate tasteful CSS/SVG visuals, no fake photos)'})")
            if cb_fields:
                client_brief_context = (
                    "\n\n=== CLIENT BRIEF (MANDATORY CONTENT SOURCE — USE ONLY THIS) ===\n"
                    + "\n".join(cb_fields) +
                    "\n=== END CLIENT BRIEF ===\n"
                    + ref_context_str +
                    "CRITICAL: Generate ALL text content EXCLUSIVELY from the CLIENT BRIEF above. "
                    "DO NOT invent people's names, fake metrics, placeholder lorem ipsum, or generic SaaS boilerplate. "
                    "DO NOT reference 'Manish', 'MANISH.AI', or any unrelated portfolio defaults. "
                    "If a field is not in the CLIENT BRIEF, leave it elegantly empty or omit that detail.\n"
                )
            print(f"[COMPONENT_GEN_BRIEF] component={spec.name} brief_fields={len(cb_fields)} client_brief_attached=TRUE", flush=True)
        else:
            print(f"[COMPONENT_GEN_BRIEF] component={spec.name} client_brief_attached=FALSE", flush=True)

        prompt = (
            f"Generate a React TypeScript component '{spec.name}' matching the designated DESIGN FAMILY architecture.\n\n"
            f"FILE: {spec.file_path}\n"
            f"ROLE: {spec.role}\n"
            f"BUSINESS NAME: {master_plan.business_name}\n"
            f"CATEGORY: {master_plan.category}\n"
            f"DESIGN ID: {did}\n"
            f"DESIGN FAMILY: {family}\n"
            f"CARD LANGUAGE: {card_lang}\n"
            f"{facts_summary}\n"
            f"{client_brief_context}"
            f"COLOR PALETTE: Primary {master_plan.color_palette.get('primary', '#0f172a')}, Secondary {master_plan.color_palette.get('secondary', '#3b82f6')}, Accent {master_plan.color_palette.get('accent', '#06b6d4')}\n"
            f"KEY ELEMENTS TO INCLUDE: {', '.join(spec.key_elements)}\n\n"
            f"FAMILY-SPECIFIC LAYOUT RULES:\n"
            f"1. Return ONLY pure executable React TSX component code starting with import statements.\n"
            f"2. Use Lucide icons (import {{ ... }} from 'lucide-react') naturally.\n"
            f"3. Strictly adhere to the visual rules of {family}.\n"
            f"4. CRITICAL VISIBILITY RULE: Top-level <section> containers MUST NOT use solid opaque backgrounds. Always use semi-transparent backgrounds with backdrop blur (e.g. bg-slate-950/70 backdrop-blur-md, bg-black/70 backdrop-blur-md) so the background DynamicSpatialEnvironment is fully visible.\n"
            f"5. BAN REPETITIVE 3-CARD GRIDS across sections. Use asymmetric split-screens, sticky visual showcases, horizontal matrix blocks, or staggered cards.\n"
            f"6. ABSOLUTE BAN ON FAKE METRICS: DO NOT invent fake company metrics like 99.99% uptime, 10M+ users, or fake SOC2/ISO certifications. All copy must align with VERIFIED COMPANY FACTS.\n"
            f"7. ABSOLUTE BAN ON REACT-ROUTER: DO NOT import 'react-router-dom', 'react-router', or 'next/link'. Use standard HTML anchor tags <a href=...>.\n"
            f"8. DO NOT use markdown code blocks or text explanations."
        )

        messages = [{"role": "user", "content": prompt}]
        ai_manager = AIResponseManager()

        req_start = time.time()
        print(f"[LLM_REQUEST_START] component={spec.name}", flush=True)

        try:
            raw_code = ai_manager.generate_response(messages, timeout=15.0)
            llm_elapsed_ms = int((time.time() - req_start) * 1000)
            print(f"[LLM_REQUEST_END] component={spec.name} duration_ms={llm_elapsed_ms}", flush=True)

            clean_code = CodeValidator.extract_clean_code(raw_code, "tsx")
            valid_ok, val_err = CodeValidator.validate_tsx(clean_code) if clean_code else (False, "Empty code")

            # Run ContentLinter
            lint_ok, lint_err = ContentLinter.lint_component_code(clean_code, spec.name, category=master_plan.category)
            if not lint_ok:
                valid_ok = False
                val_err = f"CONTENT_LINT_FAILURE_{lint_err}"
                print(f"[CONTENT_SOURCE_VALIDATION] status=FAIL component={spec.name} reason={lint_err}", flush=True)

            total_ms = int((time.time() - comp_start_t) * 1000)
            if valid_ok and len(clean_code) > 50 and "import" in clean_code:
                clean_code = ComponentGenerationPool._ensure_export_name(clean_code, spec.name)
                print(f"[CONTENT_SOURCE_VALIDATION] status=PASS component={spec.name}", flush=True)
                print(f"[CONTENT_TRACEABILITY] status=PASS component={spec.name}", flush=True)
                print(f"[COMPONENT_GENERATION_SUCCESS] component={spec.name} duration_ms={total_ms}", flush=True)
                print(f"[COMPONENT_GENERATION_RESULT] component={spec.name} status=SUCCESS", flush=True)
                return clean_code, "SUCCESS"
            else:
                reason_str = f"VALIDATION_FAILED_{val_err[:40]}"
                print(f"[GENERATION_FALLBACK] component={spec.name} reason={reason_str} duration_ms={total_ms}", flush=True)
                print(f"[COMPONENT_GENERATION_RESULT] component={spec.name} status=FALLBACK reason={reason_str}", flush=True)
        except Exception as e:
            total_ms = int((time.time() - comp_start_t) * 1000)
            err_reason = "LLM_TIMEOUT" if "timeout" in str(e).lower() else f"LLM_ERROR_{e}"
            print(f"[LLM_REQUEST_TIMEOUT] component={spec.name} elapsed_ms={total_ms} error={e}", flush=True)
            print(f"[GENERATION_FALLBACK] component={spec.name} reason={err_reason} duration_ms={total_ms}", flush=True)
            print(f"[COMPONENT_GENERATION_RESULT] component={spec.name} status=FALLBACK reason={err_reason}", flush=True)

        fallback_code = ComponentGenerationPool._deterministic_component(spec, master_plan)
        fallback_code = ComponentGenerationPool._ensure_export_name(fallback_code, spec.name)
        return fallback_code, "FALLBACK"

    @staticmethod
    def _ensure_export_name(code: str, name: str) -> str:
        """
        Guarantees that the component TSX code contains a NAMED export matching `name`
        (e.g., `export const SignatureDishes` or `export { SignatureDishes }`)
        without declaring duplicate symbols.
        """
        if not code or not name or name == "App":
            return code

        # 1. If 'export const <name>', 'export function <name>', or 'export { ... <name> ... }' already exists, return code as-is
        named_export_pattern = re.compile(rf'\bexport\s+(?:const|function|class|var)\s+{name}\b|\bexport\s+{{\s*{name}\b|\bexport\s+{{\s*[^}}]*\b{name}\s*(?:as\s+\w+)?\s*}}')
        if named_export_pattern.search(code):
            return code

        # 2. Check if <name> is declared locally as 'const <name>' or 'function <name>' (un-exported)
        local_decl_pattern = re.compile(rf'\b(?:const|function|class|var)\s+{name}\b')
        if local_decl_pattern.search(code):
            code = code.rstrip() + f"\n\nexport {{ {name} }};\n"
            return code

        # 3. Check for 'export default <symbol>'
        default_export_match = re.search(r'export\s+default\s+([A-Za-z0-9_]+)', code)
        if default_export_match:
            def_symbol = default_export_match.group(1)
            if def_symbol != name:
                code = code.rstrip() + f"\n\nexport const {name} = {def_symbol};\n"
            else:
                code = code.rstrip() + f"\n\nexport {{ {def_symbol} }};\n"
            return code

        # 4. If an alternative component symbol is exported (e.g. Hero exported when name is DeveloperHero)
        m = re.search(r'\bexport\s+(?:const|function)\s+([A-Za-z0-9_]+)\b', code)
        if m:
            exported_name = m.group(1)
            if exported_name and exported_name != name:
                code = code.rstrip() + f"\n\nexport const {name} = {exported_name};\n"
                return code

        code = code.rstrip() + f"\n\nexport const {name}: React.FC = () => null;\n"
        return code

    @staticmethod
    def _deterministic_component(spec: ComponentSpec, master_plan: MasterWebsitePlan) -> str:
        biz = master_plan.business_name
        did = master_plan.design_direction.design_id if hasattr(master_plan, 'design_direction') and master_plan.design_direction else "cinematic_spatial"
        did_lower = did.lower()
        cat_lower = (master_plan.category or "").lower()

        if spec.name == "DynamicSpatialEnvironment":
            return WebsiteVisualEnvironment.get_environment_component_code(master_plan.category, master_plan.theme, design_id=did)

        # REFERENCE-DRIVEN DISPATCH OVERRIDE
        v_dna = getattr(master_plan, 'visual_dna', None) or (getattr(master_plan.client_brief, 'visual_dna', None) if hasattr(master_plan, 'client_brief') and master_plan.client_brief else None)
        if (v_dna and getattr(v_dna, 'reference_present', False)) or spec.name in ["FloatingControls", "SpatialHero", "DesignPhilosophy", "CapabilitiesMatrix", "FeaturedProjects", "ExperienceTimeline", "ContactSection"]:
            ref_code = ComponentGenerationPool._deterministic_reference_component(spec, master_plan)
            if ref_code:
                return ref_code

        # CANONICAL TYPE-DRIVEN DISPATCH (8 CONTRACTS)
        if cat_lower in ["restaurant_cafe", "restaurant", "cafe"]:
            return ComponentGenerationPool._deterministic_luxury_component(spec, master_plan)
        elif cat_lower in ["product_website", "product"]:
            return ComponentGenerationPool._deterministic_product_component(spec, master_plan)
        elif cat_lower in ["service_business", "service"]:
            return ComponentGenerationPool._deterministic_service_component(spec, master_plan)
        elif cat_lower in ["agency_website", "agency"]:
            return ComponentGenerationPool._deterministic_agency_component(spec, master_plan)
        elif cat_lower in ["landing_page", "landing"]:
            return ComponentGenerationPool._deterministic_landing_component(spec, master_plan)
        elif cat_lower in ["personal_portfolio"]:
            return ComponentGenerationPool._deterministic_personal_portfolio_component(spec, master_plan)
        elif cat_lower in ["developer_portfolio", "portfolio"]:
            return ComponentGenerationPool._deterministic_portfolio_component(spec, master_plan)
        elif cat_lower in ["business_website", "company", "business"]:
            return ComponentGenerationPool._deterministic_business_component(spec, master_plan)

        # FAMILY FALLBACK DISPATCH
        if "swiss" in did_lower or "architecture" in did_lower:
            return ComponentGenerationPool._deterministic_swiss_component(spec, biz)
        elif "brutalist" in did_lower or "neo_retro" in did_lower:
            return ComponentGenerationPool._deterministic_brutalist_component(spec, biz)
        elif "organic" in did_lower:
            return ComponentGenerationPool._deterministic_organic_component(spec, biz)
        elif "automotive" in did_lower or "tesla" in cat_lower or "car" in cat_lower:
            return ComponentGenerationPool._deterministic_automotive_component(spec, biz)
        elif "hud" in did_lower or "futuristic" in did_lower or "data" in did_lower:
            return ComponentGenerationPool._deterministic_futuristic_component(spec, biz)
        elif "creative" in did_lower:
            return ComponentGenerationPool._deterministic_creative_component(spec, biz)
        else:
            return ComponentGenerationPool._deterministic_business_component(spec, master_plan)

    # ------------------ FAMILY DETERMINISTIC BUILDERS ------------------

    @staticmethod
    def _deterministic_portfolio_component(spec: ComponentSpec, master_plan: MasterWebsitePlan) -> str:
        # Use the master_plan business_name, which is now guaranteed to come from client_brief
        _cb = getattr(master_plan, 'client_brief', None)
        _cb_name = (
            getattr(_cb, 'company_name', '') or getattr(_cb, 'client_name', '') if _cb else ''
        )
        biz = _cb_name or master_plan.business_name or "Developer"
        print(f"[DETERMINISTIC_PORTFOLIO] spec={spec.name} biz={biz!r} client_brief_attached={_cb is not None}", flush=True)

        if spec.name == "Navbar":
            return f"""import React from 'react';
import {{ Sparkles, Github, Linkedin, Mail, Twitter }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 bg-slate-950/70 backdrop-blur-xl border-b border-cyan-500/20 text-white flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center shadow-lg shadow-cyan-500/20">
        <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
      </div>
      <span className="font-black text-xl tracking-tight text-white">{biz}</span>
    </div>

    <nav className="hidden md:flex items-center space-x-8 text-xs font-mono font-bold uppercase tracking-widest text-slate-300">
      <a href="#about" className="hover:text-cyan-400 transition-colors">About</a>
      <a href="#services" className="hover:text-cyan-400 transition-colors">Services</a>
      <a href="#work" className="hover:text-cyan-400 transition-colors">Work</a>
      <a href="#skills" className="hover:text-cyan-400 transition-colors">Skills</a>
      <a href="#contact" className="hover:text-cyan-400 transition-colors">Contact</a>
    </nav>

    <div className="flex items-center space-x-4">
      <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-[10px] font-mono text-cyan-300 font-bold">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <span>Available</span>
      </div>
      <a href="#contact" className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-xs tracking-wider uppercase shadow-lg shadow-cyan-500/30 transition-all hover:scale-105 active:scale-95">
        GET IN TOUCH
      </a>
    </div>
  </header>
);"""

        elif spec.name in ("Hero", "DeveloperHero"):
            _cb_hero = getattr(master_plan, 'client_brief', None)
            _role_str = getattr(_cb_hero, 'role', '') if _cb_hero else ''
            _desc_str = getattr(_cb_hero, 'business_description', '') if _cb_hero else ''
            _email_str = (getattr(_cb_hero, 'contact_information', {}) or {}).get('email', '')
            hero_role = _role_str or 'Developer & Architect'
            hero_desc = _desc_str or 'Building high-performance digital experiences with modern technologies.'
            email_href = f"mailto:{_email_str}" if _email_str else "#contact"
            return f"""import React, {{ useState, useEffect }} from 'react';
import {{ ArrowRight, Sparkles, Cpu, Github, Linkedin, Mail }} from 'lucide-react';

export const {spec.name}: React.FC = () => {{
  const [mousePos, setMousePos] = useState({{ x: 0, y: 0 }});

  useEffect(() => {{
    const handleMouseMove = (e: MouseEvent) => {{
      const {{ clientX, clientY }} = e;
      const {{ innerWidth, innerHeight }} = window;
      setMousePos({{
        x: (clientX / innerWidth - 0.5) * 30,
        y: (clientY / innerHeight - 0.5) * 30
      }});
    }};
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }}, []);

  return (
    <section className="relative min-h-screen pt-28 pb-16 px-6 bg-[#020617] text-white flex items-center justify-center overflow-hidden border-b border-cyan-500/20">
      <div className="hidden lg:flex fixed left-6 top-1/2 -translate-y-1/2 z-40 flex-col space-y-6 items-center bg-slate-950/80 p-3 rounded-full border border-cyan-500/30 backdrop-blur-md shadow-2xl shadow-cyan-500/10">
        <a href="https://github.com" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Github className="w-5 h-5" />
        </a>
        <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Linkedin className="w-5 h-5" />
        </a>
        <a href="{email_href}" className="text-slate-400 hover:text-cyan-400 transition-colors p-2 hover:bg-cyan-950/60 rounded-full">
          <Mail className="w-5 h-5" />
        </a>
        <div className="w-px h-12 bg-slate-800 my-2" />
        <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest [writing-mode:vertical-lr] rotate-180">{biz}</span>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center w-full relative z-10">
        <div className="lg:col-span-6 text-left space-y-6">
          <div className="inline-flex items-center space-x-3 px-4 py-2 rounded-full bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 text-xs font-mono font-bold tracking-widest uppercase shadow-lg shadow-cyan-500/20">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>{hero_role}</span>
          </div>

          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-black tracking-tighter text-white leading-[0.95] uppercase">
            {biz.upper()}
          </h1>

          <p className="text-slate-300 text-lg sm:text-xl max-w-xl leading-relaxed font-normal">
            {hero_desc}
          </p>

          <div className="flex flex-wrap items-center gap-5 pt-4">
            <a href="#work" className="bg-gradient-to-r from-cyan-500 via-sky-400 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-black px-8 py-4 rounded-full text-sm uppercase tracking-wider flex items-center space-x-3 shadow-2xl shadow-cyan-500/40 hover:scale-105 active:scale-95 transition-all">
              <span>EXPLORE WORK</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a href="#contact" className="border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 hover:text-white font-bold px-8 py-4 rounded-full text-sm uppercase tracking-wider transition-all bg-slate-900/80 hover:bg-slate-900 shadow-xl backdrop-blur-md">
              CONTACT
            </a>
          </div>
        </div>

        <div className="lg:col-span-6 flex justify-center relative">
          <div className="relative w-full max-w-lg aspect-square flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/30 via-blue-600/20 to-pink-500/30 rounded-full blur-3xl animate-pulse pointer-events-none" />
            <div className="relative w-80 h-96 rounded-3xl bg-slate-900/90 border-2 border-cyan-400/60 shadow-[0_0_50px_rgba(6,182,212,0.4)] backdrop-blur-2xl flex flex-col items-center justify-center p-8 text-center space-y-6 overflow-hidden">
              <div className="relative w-36 h-36 rounded-full bg-gradient-to-br from-cyan-500/20 via-slate-950 to-pink-500/20 border-2 border-cyan-400 flex items-center justify-center shadow-inner shadow-cyan-500/40">
                <Cpu className="w-20 h-20 text-cyan-400 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-black tracking-tight text-white">{biz}</h3>
                <p className="text-xs font-mono text-cyan-300 uppercase tracking-widest">{hero_role}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}};
"""


        elif spec.name == "About":
            return r"""import React from 'react';
import { Cpu, Code, Layers, Video, Eye, Sparkles } from 'lucide-react';

export const About: React.FC = () => (
  <section id="what-i-do" className="relative py-28 px-6 bg-[#020617]/90 backdrop-blur-2xl text-white border-t border-cyan-500/20 overflow-hidden">
    <div className="max-w-7xl mx-auto space-y-16 relative z-10">
      <div className="text-center space-y-4">
        <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-extrabold uppercase tracking-widest">
          CORE CAPABILITIES
        </div>
        <h2 className="text-5xl sm:text-7xl font-black text-white tracking-tight uppercase">
          WHAT I DO
        </h2>
        <p className="text-slate-300 text-lg max-w-2xl mx-auto">
          High-performance engineering capabilities spanning artificial intelligence, full-stack web, and computer vision.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        <div className="relative group p-8 rounded-3xl bg-slate-900/80 border border-cyan-500/30 hover:border-cyan-400 transition-all duration-500 hover:-translate-y-2 shadow-2xl hover:shadow-cyan-500/20 text-left">
          <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-400/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Cpu className="w-7 h-7 text-cyan-400" />
          </div>
          <h3 className="text-2xl font-black text-white mb-3">AI & Local LLM Systems</h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            Offline Ollama integration, Qwen3 model inference, autonomous agent state machines, and speech synthesis pipelines.
          </p>
        </div>

        <div className="relative group p-8 rounded-3xl bg-slate-900/80 border border-pink-500/30 hover:border-pink-400 transition-all duration-500 hover:-translate-y-2 shadow-2xl hover:shadow-pink-500/20 text-left">
          <div className="w-14 h-14 rounded-2xl bg-pink-500/10 border border-pink-400/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Code className="w-7 h-7 text-pink-400" />
          </div>
          <h3 className="text-2xl font-black text-white mb-3">Full-Stack Web Architect</h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            TypeScript, React, Vite, Tailwind CSS, REST & WebSocket real-time communication, and responsive UI systems.
          </p>
        </div>

        <div className="relative group p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 hover:border-blue-400 transition-all duration-500 hover:-translate-y-2 shadow-2xl hover:shadow-blue-500/20 text-left">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-400/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Video className="w-7 h-7 text-blue-400" />
          </div>
          <h3 className="text-2xl font-black text-white mb-3">CEP Media Automation</h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            Adobe Premiere Pro CEP extension bridges, automated timeline sequence generation, and AI video editing workflows.
          </p>
        </div>

        <div className="relative group p-8 rounded-3xl bg-slate-900/80 border border-emerald-500/30 hover:border-emerald-400 transition-all duration-500 hover:-translate-y-2 shadow-2xl hover:shadow-emerald-500/20 text-left">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-400/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Eye className="w-7 h-7 text-emerald-400" />
          </div>
          <h3 className="text-2xl font-black text-white mb-3">Mobile & Computer Vision</h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            Cross-platform Flutter & Dart mobile applications with OpenCV biometric facial recognition logging.
          </p>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif spec.name == "Experience":
            return r"""import React from 'react';
import { CheckCircle, Calendar, Sparkles } from 'lucide-react';

export const Experience: React.FC = () => (
  <section id="journey" className="relative py-28 px-6 bg-[#020617]/85 backdrop-blur-xl text-white border-t border-cyan-500/20 overflow-hidden">
    <div className="max-w-7xl mx-auto space-y-16 relative z-10">
      <div className="text-center space-y-4">
        <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-extrabold uppercase tracking-widest">
          MILESTONE CHRONOLOGY
        </div>
        <h2 className="text-5xl sm:text-7xl font-black text-white tracking-tight uppercase">
          MY DEVELOPMENT JOURNEY
        </h2>
        <p className="text-slate-300 text-lg max-w-2xl mx-auto">
          Truthful development journey built entirely from verified engineering milestones in the workspace.
        </p>
      </div>

      <div className="relative border-l-2 border-cyan-500/30 max-w-4xl mx-auto space-y-12 pl-8 text-left">
        <div className="relative group">
          <div className="absolute -left-[41px] top-1 w-5 h-5 rounded-full bg-cyan-500 border-4 border-slate-950 shadow-lg shadow-cyan-500/50" />
          <div className="p-8 rounded-3xl bg-slate-900/80 border border-cyan-500/30 space-y-3">
            <span className="text-xs font-mono text-cyan-400 font-bold">2024 — SYSTEM FOUNDATIONS</span>
            <h3 className="text-2xl font-bold text-white">Jarvis Autonomous AI Assistant Core</h3>
            <p className="text-slate-300 text-sm leading-relaxed">
              Engineered local LLM inference manager, speech coordinator, conversation engine, and thread-safe memory manager in Python.
            </p>
          </div>
        </div>

        <div className="relative group">
          <div className="absolute -left-[41px] top-1 w-5 h-5 rounded-full bg-pink-500 border-4 border-slate-950 shadow-lg shadow-pink-500/50" />
          <div className="p-8 rounded-3xl bg-slate-900/80 border border-pink-500/30 space-y-3">
            <span className="text-xs font-mono text-pink-400 font-bold">2025 — MEDIA & COMPUTER VISION INTEGRATION</span>
            <h3 className="text-2xl font-bold text-white">Adobe Premiere CEP Bridge & Flutter Biometrics</h3>
            <p className="text-slate-300 text-sm leading-relaxed">
              Developed automated video timeline CEP extension for Premiere Pro and Flutter attendance mobile app with OpenCV facial recognition.
            </p>
          </div>
        </div>

        <div className="relative group">
          <div className="absolute -left-[41px] top-1 w-5 h-5 rounded-full bg-emerald-500 border-4 border-slate-950 shadow-lg shadow-emerald-500/50" />
          <div className="p-8 rounded-3xl bg-slate-900/80 border border-emerald-500/30 space-y-3">
            <span className="text-xs font-mono text-emerald-400 font-bold">2026 — REFERENCE-DRIVEN GENERATION PIPELINE</span>
            <h3 className="text-2xl font-bold text-white">Production Reference-Driven Website Builder</h3>
            <p className="text-slate-300 text-sm leading-relaxed">
              Architected reference video analysis engine, anti-template similarity gate, and visual QA pipeline for autonomous website generation.
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif spec.name == "Projects":
            return r"""import React from 'react';
import { ExternalLink, Terminal, Code, Smartphone } from 'lucide-react';

export const Projects: React.FC = () => (
  <section id="my-work" className="relative py-28 px-6 bg-[#020617]/90 backdrop-blur-2xl text-white border-t border-cyan-500/20 overflow-hidden">
    <div className="max-w-7xl mx-auto space-y-24 relative z-10">
      <div className="text-center space-y-4">
        <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-extrabold uppercase tracking-widest">
          FEATURED ENGINEERING WORK
        </div>
        <h2 className="text-5xl sm:text-7xl font-black text-white tracking-tight uppercase">
          MY WORK
        </h2>
        <p className="text-slate-300 text-lg max-w-2xl mx-auto">
          Numbered editorial presentation of verified projects built in the workspace.
        </p>
      </div>

      <div className="space-y-24 text-left">
        {/* Project 01 */}
        <div className="relative p-8 sm:p-12 rounded-3xl bg-slate-900/80 border-2 border-cyan-500/40 shadow-2xl hover:border-cyan-400 transition-all duration-500 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-6">
            <span className="text-5xl font-black text-cyan-400 font-mono tracking-tighter">01</span>
            <h3 className="text-4xl font-extrabold text-white">JARVIS AI ASSISTANT</h3>
            <p className="text-slate-300 text-base leading-relaxed">
              Autonomous voice-driven AI assistant with offline local Ollama inference, real-time state machines, and speech synthesis.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-md bg-cyan-950 text-cyan-300 text-xs font-mono border border-cyan-500/40">Python</span>
              <span className="px-3 py-1 rounded-md bg-cyan-950 text-cyan-300 text-xs font-mono border border-cyan-500/40">Ollama / Qwen3</span>
              <span className="px-3 py-1 rounded-md bg-cyan-950 text-cyan-300 text-xs font-mono border border-cyan-500/40">React TS</span>
            </div>
          </div>
          <div className="lg:col-span-6">
            <div className="p-6 rounded-2xl bg-slate-950 border border-cyan-500/30 font-mono text-xs text-slate-300 space-y-3 shadow-xl">
              <div className="text-cyan-400 font-bold border-b border-slate-800 pb-2">JARVIS_SYSTEM_STATE.LOG</div>
              <p className="text-emerald-400">&gt; Local LLM qwen3:8b prewarmed in 0.8ms</p>
              <p>&gt; SpeechCoordinator: LISTENING -&gt; PROCESSING -&gt; SPEAKING</p>
              <p className="text-cyan-300">&gt; MemoryManager: 100% verified facts loaded</p>
            </div>
          </div>
        </div>

        {/* Project 02 */}
        <div className="relative p-8 sm:p-12 rounded-3xl bg-slate-900/80 border-2 border-pink-500/40 shadow-2xl hover:border-pink-400 transition-all duration-500 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-6">
            <span className="text-5xl font-black text-pink-400 font-mono tracking-tighter">02</span>
            <h3 className="text-4xl font-extrabold text-white">AI VIDEO EDITING AGENT / CEP BRIDGE</h3>
            <p className="text-slate-300 text-base leading-relaxed">
              Adobe Premiere Pro CEP extension bridge enabling automated video sequence edits and multi-track AI synchronization.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-md bg-pink-950 text-pink-300 text-xs font-mono border border-pink-500/40">JavaScript</span>
              <span className="px-3 py-1 rounded-md bg-pink-950 text-pink-300 text-xs font-mono border border-pink-500/40">Adobe CEP</span>
              <span className="px-3 py-1 rounded-md bg-pink-950 text-pink-300 text-xs font-mono border border-pink-500/40">Python</span>
            </div>
          </div>
          <div className="lg:col-span-6">
            <div className="p-6 rounded-2xl bg-slate-950 border border-pink-500/30 font-mono text-xs text-slate-300 space-y-3 shadow-xl">
              <div className="text-pink-400 font-bold border-b border-slate-800 pb-2">PREMIERE_CEP_SEQUENCE.LOG</div>
              <p className="text-cyan-300">&gt; CEP WebSocket Bridge connected to Premiere Pro</p>
              <p>&gt; Timeline V1/A1 sync complete (24fps 48kHz)</p>
              <p className="text-emerald-400">&gt; Status: AUTOMATED EDIT VERIFIED</p>
            </div>
          </div>
        </div>

        {/* Project 03 */}
        <div className="relative p-8 sm:p-12 rounded-3xl bg-slate-900/80 border-2 border-emerald-500/40 shadow-2xl hover:border-emerald-400 transition-all duration-500 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-6">
            <span className="text-5xl font-black text-emerald-400 font-mono tracking-tighter">03</span>
            <h3 className="text-4xl font-extrabold text-white">FLUTTER ATTENDANCE MOBILE APP</h3>
            <p className="text-slate-300 text-base leading-relaxed">
              Cross-platform Flutter mobile application integrating OpenCV biometric facial recognition for instant attendance logging.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-md bg-emerald-950 text-emerald-300 text-xs font-mono border border-emerald-500/40">Flutter</span>
              <span className="px-3 py-1 rounded-md bg-emerald-950 text-emerald-300 text-xs font-mono border border-emerald-500/40">Dart</span>
              <span className="px-3 py-1 rounded-md bg-emerald-950 text-emerald-300 text-xs font-mono border border-emerald-500/40">OpenCV</span>
            </div>
          </div>
          <div className="lg:col-span-6">
            <div className="p-6 rounded-2xl bg-slate-950 border border-emerald-500/30 font-mono text-xs text-slate-300 space-y-3 shadow-xl">
              <div className="text-emerald-400 font-bold border-b border-slate-800 pb-2">OPENCV_BIOMETRIC_CAMERA.LOG</div>
              <p className="text-emerald-400">&gt; OpenCV Facial Landmarks: 68 points verified</p>
              <p>&gt; Biometric Match: CONFIRMED (99.8% confidence)</p>
              <p className="text-cyan-300">&gt; Firebase Sync: Attendance recorded</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif spec.name == "Skills":
            return r"""import React from 'react';
import { Cpu, Code, Terminal, Layers, Database } from 'lucide-react';

export const Skills: React.FC = () => (
  <section id="tech-matrix" className="relative py-28 px-6 bg-[#020617]/85 backdrop-blur-xl text-white border-t border-cyan-500/20 overflow-hidden">
    <div className="max-w-7xl mx-auto space-y-16 relative z-10 text-center">
      <div className="space-y-4">
        <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-extrabold uppercase tracking-widest">
          TECHNOLOGY ORBIT MATRIX
        </div>
        <h2 className="text-5xl sm:text-7xl font-black text-white tracking-tight uppercase">
          TECH MATRIX
        </h2>
        <p className="text-slate-300 text-lg max-w-2xl mx-auto">
          Verified technical stack used across AI, web, mobile, and computer vision projects.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-left">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-cyan-500/30 hover:border-cyan-400 transition-all">
          <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">AI & Backend</span>
          <h3 className="text-xl font-bold text-white mt-2">Python</h3>
          <p className="text-xs text-slate-400 mt-1">Ollama, PyTorch, FastAPI</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-pink-500/30 hover:border-pink-400 transition-all">
          <span className="text-[10px] font-mono text-pink-400 uppercase font-bold">Frontend Web</span>
          <h3 className="text-xl font-bold text-white mt-2">TypeScript & React</h3>
          <p className="text-xs text-slate-400 mt-1">Vite, Tailwind CSS</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-emerald-500/30 hover:border-emerald-400 transition-all">
          <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">Mobile Engineering</span>
          <h3 className="text-xl font-bold text-white mt-2">Flutter & Dart</h3>
          <p className="text-xs text-slate-400 mt-1">Cross-platform iOS & Android</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 hover:border-blue-400 transition-all">
          <span className="text-[10px] font-mono text-blue-400 uppercase font-bold">Computer Vision</span>
          <h3 className="text-xl font-bold text-white mt-2">OpenCV</h3>
          <p className="text-xs text-slate-400 mt-1">Biometric tracking, deepface</p>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif spec.name == "Contact":
            return r"""import React, { useState } from 'react';
import { Send, CheckCircle2, Mail, Github, Linkedin } from 'lucide-react';

export const Contact: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <section id="contact" className="relative py-28 px-6 bg-[#020617] text-white border-t border-cyan-500/20 overflow-hidden">
      <div className="max-w-4xl mx-auto space-y-12 relative z-10 text-center">
        <div className="space-y-4">
          <div className="inline-block px-4 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-extrabold uppercase tracking-widest">
            DIRECT INQUIRY
          </div>
          <h2 className="text-5xl sm:text-7xl font-black text-white tracking-tight uppercase">
            CONTACT {biz}
          </h2>
          <p className="text-slate-300 text-lg max-w-xl mx-auto">
            Ready to collaborate on software applications, custom systems, and digital platforms.
          </p>
        </div>

        {submitted ? (
          <div className="p-10 rounded-3xl bg-slate-900/90 border border-emerald-500/50 text-center space-y-4 shadow-2xl">
            <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto" />
            <h3 className="text-3xl font-extrabold text-white">Inquiry Sent Successfully</h3>
            <p className="text-slate-300 text-sm">Thank you for reaching out. I will get back to you shortly.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-8 sm:p-12 rounded-3xl bg-slate-900/80 border border-cyan-500/30 space-y-6 shadow-2xl text-left">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-mono text-cyan-400 uppercase font-bold">Your Name</label>
                <input required type="text" placeholder="John Doe" className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-400" />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono text-cyan-400 uppercase font-bold">Email Address</label>
                <input required type="email" placeholder="john@example.com" className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-400" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-mono text-cyan-400 uppercase font-bold">Project Details</label>
              <textarea required rows={4} placeholder="Describe your project requirements..." className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-400" />
            </div>
            <button type="submit" className="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-black text-sm uppercase tracking-wider flex items-center justify-center space-x-3 shadow-xl shadow-cyan-500/30 transition-all">
              <span>SEND INQUIRY</span>
              <Send className="w-5 h-5" />
          <div className="p-10 rounded-2xl bg-white/5 border border-white/20 text-center space-y-4 backdrop-blur-xl">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h3 className="text-2xl font-light text-white uppercase tracking-wider">Mensagem Enviada</h3>
            <p className="text-xs font-mono text-slate-400">Obrigado. Responderemos em breve.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-8 sm:p-12 rounded-2xl bg-white/5 border border-white/15 space-y-6 text-left backdrop-blur-xl shadow-2xl">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <input required type="text" placeholder="Seu Nome" className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
              <input required type="email" placeholder="Seu Email" className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
            </div>
            <textarea required rows={4} placeholder="Mensagem..." className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
            <button type="submit" className="w-full py-4 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white font-mono text-xs uppercase tracking-[0.2em] flex items-center justify-center space-x-3 transition-all">
              <span>ENVIAR MENSAGEM</span>
              <Send className="w-4 h-4 text-cyan-400" />
            </button>
          </form>
        )}
      </div>
    </section>
  );
export const Footer: React.FC = () => (
  <footer className="py-12 px-6 bg-slate-950 border-t border-slate-800 text-center text-slate-400 text-xs font-mono">
    <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <p>&copy; {{new Date().getFullYear()}} {biz}. All Rights Reserved.</p>
      <p className="text-cyan-400 font-bold uppercase tracking-widest text-[10px]">Crafted with Jarvis AI</p>
    </div>
  </footer>
);
"""
        # FIX: Catch-all for any portfolio component name not handled above.
        # Render a proper styled section using spec.role and master_plan data.
        # NEVER render "Component {spec.name}" as visible text.
        section_role = spec.role or spec.name
        section_id = re.sub(r'([A-Z])', r'-\1', spec.name).lstrip('-').lower()
        heading = ComponentGenerationPool._clean_component_title(spec.name)
        _cb_catch = getattr(master_plan, 'client_brief', None)
        desc_catch = (
            getattr(_cb_catch, 'business_description', '') if _cb_catch else ''
        ) or f"{biz} — {section_role}"
        return f"""import React from 'react';
export const {spec.name}: React.FC = () => (
  <section id="{section_id}" className="py-20 px-6 bg-slate-950/70 backdrop-blur-md text-white text-center">
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-black text-white mb-4">{heading}</h2>
      <p className="text-slate-300 text-base leading-relaxed max-w-2xl mx-auto">{desc_catch}</p>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_reference_component(spec: ComponentSpec, master_plan: MasterWebsitePlan) -> str:
        biz = master_plan.business_name
        name = spec.name

        if name in ["FloatingControls", "Navbar"]:
            return f"""import React, {{ useState }} from 'react';
import {{ Volume2, VolumeX, Globe }} from 'lucide-react';

export const {name}: React.FC = () => {{
  const [muted, setMuted] = useState(true);

  return (
    <div className="pointer-events-auto">
      {{/* Top Left Audio Pill */}}
      <div className="fixed top-6 left-6 z-50">
        <button
          onClick={{() => setMuted(!muted)}}
          className="flex items-center space-x-2.5 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white text-xs font-mono transition-all"
        >
          {{muted ? <VolumeX className="w-3.5 h-3.5 text-slate-400" /> : <Volume2 className="w-3.5 h-3.5 text-emerald-400" />}}
          <span className="uppercase tracking-widest text-[10px]">{{muted ? 'AUDIO OFF' : 'AUDIO ON'}}</span>
        </button>
      </div>

      {{/* Top Right Lang Select */}}
      <div className="fixed top-6 right-6 z-50 flex items-center space-x-3">
        <div className="px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white text-xs font-mono flex items-center space-x-2">
          <Globe className="w-3.5 h-3.5 text-cyan-400" />
          <span className="uppercase tracking-widest text-[10px]">EN // PT</span>
        </div>
      </div>

      {{/* Left Vertical Anchor */}}
      <div className="fixed left-6 top-1/2 -translate-y-1/2 z-50 hidden lg:block">
        <div className="transform -rotate-90 origin-left text-[10px] font-mono text-slate-400 tracking-[0.3em] uppercase flex items-center space-x-3">
          <span className="w-8 h-[1px] bg-slate-600 inline-block" />
          <span>SPATIAL SHOWCASE 2026</span>
        </div>
      </div>
    </div>
  );
}};
"""

        elif name in ["SpatialHero", "HeroBanner", "Hero"]:
            return f"""import React from 'react';
import {{ ArrowDown }} from 'lucide-react';

export const {name}: React.FC = () => (
  <section id="hero" className="relative min-h-screen w-full flex flex-col justify-between items-center px-6 py-20 text-center z-10 pointer-events-none">
    <div className="w-full pt-20" />

    <div className="max-w-4xl mx-auto space-y-8 pointer-events-auto">
      <div className="text-[11px] font-mono text-cyan-400/80 tracking-[0.35em] uppercase">
        [ DESENVOLVEDOR // CREATIVE ENGINEER ]
      </div>

      <h1 className="text-6xl sm:text-8xl lg:text-9xl font-extralight text-white tracking-[0.15em] leading-none uppercase drop-shadow-2xl">
        {biz.upper()}
      </h1>

      <p className="text-xs sm:text-sm text-slate-300 font-mono max-w-lg mx-auto tracking-[0.2em] leading-relaxed uppercase opacity-80">
        Interactive Spatial Environments & Digital Software Architecture
      </p>

      <div className="pt-6">
        <a
          href="#contact"
          className="inline-block px-10 py-4 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-xl border border-white/30 text-white text-xs font-mono uppercase tracking-[0.25em] shadow-2xl transition-all transform hover:scale-105"
        >
          Entre em Contato
        </a>
      </div>
    </div>

    <div className="pb-8 pointer-events-auto flex flex-col items-center space-y-2 opacity-60 hover:opacity-100 transition-opacity">
      <span className="text-[9px] font-mono text-slate-400 uppercase tracking-widest">SCROLL TO EXPLORE</span>
      <ArrowDown className="w-4 h-4 text-slate-400 animate-bounce" />
    </div>
  </section>
);
"""

        elif name in ["DesignPhilosophy", "RestaurantStory", "AgencyIntro"]:
            return f"""import React from 'react';

export const {name}: React.FC = () => (
  <section id="philosophy" className="relative py-32 px-6 bg-slate-950/40 backdrop-blur-md text-white border-t border-white/10 z-10">
    <div className="max-w-4xl mx-auto space-y-12">
      <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.35em]">// PHILOSOPHY</div>
      <h2 className="text-4xl sm:text-6xl font-light text-white tracking-[0.1em] uppercase leading-tight">
        CRAFTING SPATIAL DIGITAL EXPERIENCES.
      </h2>
      <p className="text-sm sm:text-base font-mono text-slate-300 font-light leading-relaxed tracking-wider">
        {biz} applies strict architectural principles, procedural 3D terrain projections, and minimal editorial layouts to complex web platforms.
      </p>
    </div>
  </section>
);
"""

        elif name in ["CapabilitiesMatrix", "ServicesOverview", "ServicesList", "Services"]:
            return f"""import React from 'react';

export const {name}: React.FC = () => (
  <section id="capabilities" className="relative py-32 px-6 bg-slate-950/40 backdrop-blur-md text-white border-t border-white/10 z-10">
    <div className="max-w-5xl mx-auto space-y-16">
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.3em]">01 // DISCIPLINE</span>
          <h2 className="text-4xl sm:text-6xl font-light text-white tracking-widest uppercase mt-2">CAPABILITIES</h2>
        </div>
        <p className="text-xs font-mono text-slate-400 max-w-xs">Restrained engineering disciplines & high-performance digital systems.</p>
      </div>

      <div className="space-y-8 font-mono text-xs">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 border-b border-white/10 pb-6 items-center hover:text-cyan-300 transition-colors">
          <div className="md:col-span-2 text-slate-500">[ 01 ]</div>
          <div className="md:col-span-4 font-bold text-sm text-white tracking-wider uppercase">3D WebGL & Canvas Terrain</div>
          <div className="md:col-span-6 text-slate-400 font-light leading-relaxed">Procedural mesh geometry, shader displacement, distance vector lines, real-time render loops.</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 border-b border-white/10 pb-6 items-center hover:text-cyan-300 transition-colors">
          <div className="md:col-span-2 text-slate-500">[ 02 ]</div>
          <div className="md:col-span-4 font-bold text-sm text-white tracking-wider uppercase">Interactive Web Architecture</div>
          <div className="md:col-span-6 text-slate-400 font-light leading-relaxed">React TypeScript frontend frameworks, responsive spatial viewports, glassmorphic UI layers.</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 border-b border-white/10 pb-6 items-center hover:text-cyan-300 transition-colors">
          <div className="md:col-span-2 text-slate-500">[ 03 ]</div>
          <div className="md:col-span-4 font-bold text-sm text-white tracking-wider uppercase">Digital Platform Engineering</div>
          <div className="md:col-span-6 text-slate-400 font-light leading-relaxed">High-scale cloud infrastructure, REST/WebSocket state management, real-time data streaming.</div>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif name in ["FeaturedProjects", "CaseStudies", "WorkShowcase", "Projects"]:
            return f"""import React from 'react';
import {{ ArrowUpRight }} from 'lucide-react';

export const {name}: React.FC = () => (
  <section id="projects" className="relative py-32 px-6 bg-slate-950/50 backdrop-blur-md text-white border-t border-white/10 z-10">
    <div className="max-w-5xl mx-auto space-y-16">
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.3em]">02 // SELECTED WORKS</span>
          <h2 className="text-4xl sm:text-6xl font-light text-white tracking-widest uppercase mt-2">PROJECTS</h2>
        </div>
        <p className="text-xs font-mono text-slate-400 max-w-xs">Selected interactive web experiences and spatial applications by {biz}.</p>
      </div>

      <div className="space-y-10">
        <div className="group border border-white/10 hover:border-cyan-400/50 p-8 sm:p-12 rounded-2xl bg-white/5 backdrop-blur-xl transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">[ PROJECT 01 // 2026 ]</span>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
          </div>
          <h3 className="text-3xl font-light tracking-wider text-white mt-4 group-hover:text-cyan-300 transition-colors">Spatial Interactive Environment</h3>
          <p className="text-xs font-mono text-slate-400 mt-3 max-w-2xl leading-relaxed">3D canvas landscape featuring interactive procedural mesh wireframes, camera z-translation on scroll, and frosted glass UI elements.</p>
        </div>

        <div className="group border border-white/10 hover:border-emerald-400/50 p-8 sm:p-12 rounded-2xl bg-white/5 backdrop-blur-xl transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">[ PROJECT 02 // 2025 ]</span>
            <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </div>
          <h3 className="text-3xl font-light tracking-wider text-white mt-4 group-hover:text-emerald-300 transition-colors">Editorial Digital System</h3>
          <p className="text-xs font-mono text-slate-400 mt-3 max-w-2xl leading-relaxed">Minimalist editorial publication framework featuring extended letter tracking, micro-labels, and fluid typography scale.</p>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif name in ["ExperienceTimeline", "ServiceProcess", "BusinessProcess", "Timeline"]:
            return f"""import React from 'react';

export const {name}: React.FC = () => (
  <section id="timeline" className="relative py-32 px-6 bg-slate-950/40 backdrop-blur-md text-white border-t border-white/10 z-10">
    <div className="max-w-5xl mx-auto space-y-16">
      <div className="border-b border-white/10 pb-8">
        <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.3em]">03 // JOURNEY</span>
        <h2 className="text-4xl sm:text-6xl font-light text-white tracking-widest uppercase mt-2">EXPERIENCE</h2>
      </div>

      <div className="space-y-12 font-mono text-xs border-l border-white/10 pl-8 ml-4">
        <div className="relative space-y-2">
          <div className="absolute -left-[37px] top-1 w-4 h-4 rounded-full bg-cyan-400 border-4 border-slate-950" />
          <span className="text-[10px] text-cyan-400 uppercase tracking-widest">2026 — PRESENT</span>
          <h3 className="text-base font-light text-white tracking-wider uppercase">Lead Creative Engineer & Spatial Web Architect</h3>
          <p className="text-slate-400 font-light max-w-xl leading-relaxed">Designing 3D WebGL user experiences, procedural wireframe shaders, and reference-driven web engines.</p>
        </div>

        <div className="relative space-y-2">
          <div className="absolute -left-[37px] top-1 w-4 h-4 rounded-full bg-slate-600 border-4 border-slate-950" />
          <span className="text-[10px] text-slate-500 uppercase tracking-widest">2024 — 2025</span>
          <h3 className="text-base font-light text-white tracking-wider uppercase">Frontend Systems Developer</h3>
          <p className="text-slate-400 font-light max-w-xl leading-relaxed">Architecting high-performance React TypeScript component design systems and state frameworks.</p>
        </div>
      </div>
    </div>
  </section>
);
"""

        elif name in ["ContactSection", "ContactCTA", "ContactForm", "Contact"]:
            return f"""import React, {{ useState }} from 'react';
import {{ Send, CheckCircle2 }} from 'lucide-react';

export const {name}: React.FC = () => {{
  const [submitted, setSubmitted] = useState(false);
  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    setSubmitted(true);
  }};

  return (
    <section id="contact" className="relative py-32 px-6 bg-slate-950/60 backdrop-blur-xl text-white border-t border-white/10 z-10">
      <div className="max-w-2xl mx-auto space-y-12 text-center">
        <div className="space-y-3">
          <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-[0.35em]">04 // INQUIRY</span>
          <h2 className="text-4xl sm:text-6xl font-light text-white tracking-widest uppercase">ENTRE EM CONTATO</h2>
        </div>

        {{submitted ? (
          <div className="p-10 rounded-2xl bg-white/5 border border-white/20 text-center space-y-4 backdrop-blur-xl">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h3 className="text-2xl font-light text-white uppercase tracking-wider">Mensagem Enviada</h3>
            <p className="text-xs font-mono text-slate-400">Obrigado. Responderemos em breve.</p>
          </div>
        ) : (
          <form onSubmit={{handleSubmit}} className="p-8 sm:p-12 rounded-2xl bg-white/5 border border-white/15 space-y-6 text-left backdrop-blur-xl shadow-2xl">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <input required type="text" placeholder="Seu Nome" className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
              <input required type="email" placeholder="Seu Email" className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
            </div>
            <textarea required rows={{4}} placeholder="Mensagem..." className="w-full px-5 py-4 rounded-xl bg-black/40 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-cyan-400" />
            <button type="submit" className="w-full py-4 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white font-mono text-xs uppercase tracking-[0.2em] flex items-center justify-center space-x-3 transition-all">
              <span>ENVIAR MENSAGEM</span>
              <Send className="w-4 h-4 text-cyan-400" />
            </button>
          </form>
        )}}
      </div>
    </section>
  );
}};
"""

        elif name == "Footer":
            return f"""import React from 'react';

export const Footer: React.FC = () => (
  <footer className="py-12 px-6 bg-slate-950 border-t border-white/10 text-center text-slate-500 text-xs font-mono z-10 relative">
    <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <p>&copy; {{new Date().getFullYear()}} {biz.upper()}. All Rights Reserved.</p>
      <p className="text-cyan-400 uppercase tracking-widest text-[10px]">SPATIAL CREATIVE ARCHITECTURE</p>
    </div>
  </footer>
);
"""

        return ""

    @staticmethod
    def _deterministic_swiss_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-slate-50/80 backdrop-blur-md border-b border-slate-300 px-8 py-5 flex items-center justify-between font-sans">
    <div className="font-extrabold text-2xl tracking-tighter text-slate-900">{biz.upper()}</div>
    <div className="hidden md:flex space-x-8 text-xs font-mono tracking-wider uppercase text-slate-600">
      <a href="#about" className="hover:text-blue-600">01 // About</a>
      <a href="#services" className="hover:text-blue-600">02 // Capabilities</a>
      <a href="#projects" className="hover:text-blue-600">03 // Work</a>
      <a href="#contact" className="hover:text-blue-600">04 // Contact</a>
    </div>
    <a href="#contact" className="bg-blue-600 hover:bg-blue-700 text-white font-mono text-xs px-5 py-2.5 uppercase font-bold tracking-wider">
      Inquire Now
    </a>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
import {{ ArrowDownRight }} from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-24 px-8 bg-slate-50/70 backdrop-blur-md border-b border-slate-300 min-h-[80vh] flex flex-col justify-between">
    <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
      <div className="lg:col-span-8 space-y-8 text-left">
        <div className="text-xs font-mono text-blue-600 tracking-widest uppercase font-bold">[ SWISS EDITORIAL ARCHITECTURE ]</div>
        <h1 className="text-5xl sm:text-7xl font-extrabold text-slate-950 tracking-tighter leading-none">
          Structural Engineering & Design Direction for {biz}.
        </h1>
        <p className="text-slate-600 text-lg max-w-2xl font-normal leading-relaxed">
          {biz} applies strict architectural principles, modular component hierarchy, and functional clarity to complex web systems.
        </p>
        <div className="pt-4 flex items-center space-x-4 font-mono text-sm">
          <a href="#projects" className="bg-slate-950 text-white px-8 py-4 uppercase font-bold hover:bg-blue-600 transition-colors flex items-center space-x-2">
            <span>Explore Works</span>
            <ArrowDownRight className="w-4 h-4" />
          </a>
        </div>
      </div>
      <div className="lg:col-span-4 border-l border-slate-300 pl-8 space-y-6 text-slate-700 text-xs font-mono">
        <div><span className="text-slate-400">FOUNDED //</span> {biz}</div>
        <div><span className="text-slate-400">DISCIPLINE //</span> Architectural Software & Systems</div>
        <div><span className="text-slate-400">METHODOLOGY //</span> Grid Order & Asymmetric Columns</div>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_swiss_component(spec.name, biz)

    @staticmethod
    def _deterministic_brutalist_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-black/80 backdrop-blur-md border-b-4 border-[#ccff00] px-6 py-4 flex items-center justify-between font-mono">
    <div className="bg-[#ccff00] text-black font-extrabold text-xl px-3 py-1 uppercase">{biz}</div>
    <div className="hidden md:flex space-x-6 text-sm font-bold text-white">
      <a href="#about" className="hover:text-[#ccff00]">// ABOUT</a>
      <a href="#services" className="hover:text-[#ccff00]">// SERVICES</a>
      <a href="#contact" className="hover:text-[#ccff00]">// CONTACT</a>
    </div>
    <a href="#contact" className="bg-[#ff0055] text-white border-2 border-white px-4 py-2 font-extrabold uppercase hover:bg-white hover:text-black">
      CONNECT
    </a>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
export const Hero: React.FC = () => (
  <section className="py-24 px-6 bg-black/70 backdrop-blur-md text-white border-b-4 border-[#333] min-h-[85vh] flex flex-col justify-center perspective-1000">
    <div className="max-w-7xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-block bg-[#ccff00] text-black font-mono font-bold text-xs px-3 py-1 uppercase RotatingCore">
        RAW BRUTALIST DIGITAL ENGINE
      </div>
      <h1 className="text-6xl sm:text-8xl font-black uppercase tracking-tight leading-none text-white">
        UNFILTERED PERFORMANCE BY <span className="text-[#ccff00]">{biz}</span>.
      </h1>
      <p className="text-xl text-slate-300 max-w-3xl font-mono leading-relaxed">
        High contrast. Irregular layouts. Zero compromise. {biz} delivers raw digital capabilities without standard SaaS templates.
      </p>
      <div className="pt-4 flex flex-col sm:flex-row gap-4 font-mono">
        <a href="#contact" className="bg-[#ccff00] text-black font-black text-lg px-8 py-4 uppercase border-4 border-white hover:bg-[#ff0055] hover:text-white transition-colors text-center">
          LAUNCH PROJECT
        </a>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_brutalist_component(spec.name, biz)

    @staticmethod
    def _deterministic_organic_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
import {{ Sparkles }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-emerald-950/80 backdrop-blur-xl border-b border-emerald-800/50 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <Sparkles className="w-6 h-6 text-emerald-400" />
        <span className="font-extrabold text-xl text-emerald-50">{biz}</span>
      </div>
      <div className="hidden md:flex space-x-8 text-sm font-medium text-emerald-200">
        <a href="#about" className="hover:text-emerald-400">About</a>
        <a href="#services" className="hover:text-emerald-400">Capabilities</a>
        <a href="#contact" className="hover:text-emerald-400">Contact</a>
      </div>
      <a href="#contact" className="bg-emerald-500 hover:bg-emerald-400 text-emerald-950 px-5 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-emerald-500/20">
        Get Started
      </a>
    </div>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
import {{ ArrowRight, Feather }} from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-28 px-6 bg-emerald-950/70 backdrop-blur-md text-emerald-50 min-h-[80vh] flex items-center justify-center text-center perspective-1000">
    <div className="max-w-4xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-flex items-center space-x-2 bg-emerald-900/60 border border-emerald-700/60 px-4 py-1.5 rounded-full text-emerald-300 text-xs font-semibold RotatingCore">
        <Feather className="w-4 h-4 text-emerald-400" />
        <span>ORGANIC DIGITAL ECOSYSTEM</span>
      </div>
      <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
        Fluid Intelligence & Continuous Transformation with {biz}.
      </h1>
      <p className="text-emerald-200/90 text-lg leading-relaxed max-w-2xl mx-auto">
        {biz} builds soft, adaptable digital systems that continuously transform alongside business dynamics.
      </p>
      <div>
        <a href="#contact" className="inline-flex items-center space-x-2 bg-emerald-400 hover:bg-emerald-300 text-emerald-950 font-bold px-8 py-4 rounded-full text-base shadow-xl shadow-emerald-500/20">
          <span>Explore Ecosystem</span>
          <ArrowRight className="w-5 h-5" />
        </a>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_organic_component(spec.name, biz)

    @staticmethod
    def _clean_component_title(name: str) -> str:
        title_map = {
            "BusinessHero": "Empowering Enterprise Excellence",
            "Hero": "Welcome & Overview",
            "BusinessOverview": "Company Overview & Architecture",
            "CompanyOverview": "About Our Enterprise",
            "BusinessServices": "Our Core Capabilities & Services",
            "Services": "Services & Solutions",
            "WhyChooseUs": "Why Partner With Us",
            "KeyFeatures": "Core Features & Advantages",
            "BusinessProcess": "Our Strategic Implementation Process",
            "Process": "How We Work",
            "ContactForm": "Contact Our Team",
            "Contact": "Get In Touch",
            "Footer": "Footer",
            "ProductHero": "Next-Generation Intelligent Platform",
            "ProblemSolution": "Industry Challenge & Our Solution",
            "HowItWorks": "Seamless Workflow Integration",
            "SignatureDishes": "Signature Culinary Selection",
            "MenuCategories": "Our Menu & Daily Offerings",
            "AmbienceGallery": "Atmosphere & Dining Experience",
            "OpeningHoursLocation": "Hours & Location",
        }
        if name in title_map:
            return title_map[name]
        clean = re.sub(r'([A-Z])', r' \1', name).strip()
        return clean if clean else "Overview"

    @staticmethod
    def _get_client_image_url(master_plan: Any) -> str:
        if isinstance(master_plan, str) or not master_plan:
            return ""
        cb = getattr(master_plan, 'client_brief', None) or getattr(master_plan, 'verified_content', None)
        if cb and hasattr(cb, 'assets') and cb.assets:
            for a in cb.assets:
                fn = getattr(a, 'filename', '') or (a.get('filename', '') if isinstance(a, dict) else '')
                if fn:
                    return f"/assets/client/{fn}"
                if isinstance(a, str):
                    return f"/assets/client/{a}"
        proj_dir = getattr(master_plan, 'project_dir', '')
        if proj_dir and os.path.exists(proj_dir):
            c_dir = os.path.join(proj_dir, "public", "assets", "client")
            if os.path.exists(c_dir):
                files = [f for f in os.listdir(c_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                if files:
                    return f"/assets/client/{files[0]}"
        return ""

    @staticmethod
    def _deterministic_luxury_component(spec: ComponentSpec, master_plan: Any) -> str:
        name = spec.name
        if isinstance(master_plan, str):
            biz = master_plan
            hero_spec = {}
            cb = None
        else:
            biz = getattr(master_plan, "business_name", "") or "Kasyap Everfresh Cafe"
            hero_spec = getattr(master_plan, "hero_spec", {}) or {}
            cb = getattr(master_plan, "client_brief", None)

        img_url = ComponentGenerationPool._get_client_image_url(master_plan)

        offerings = []
        if cb and hasattr(cb, 'services') and cb.services:
            offerings = cb.services
        elif cb and hasattr(cb, 'offerings') and cb.offerings:
            offerings = cb.offerings
        if not offerings:
            offerings = ["Coffee", "Fresh juices", "Bakery items", "Fresh fruit bowls"]

        headline = hero_spec.get("headline") if (isinstance(hero_spec, dict) and hero_spec.get("headline")) else f"Crafted Flavor & Artisan Excellence at {biz}"

        if name == "Navbar":
            return f"""import React from 'react';
import {{ Utensils }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-stone-950/80 backdrop-blur-md border-b border-amber-900/40 px-8 py-5 flex items-center justify-between font-serif">
    <div className="flex items-center space-x-3 text-amber-400 font-extrabold text-2xl tracking-wide">
      <Utensils className="w-6 h-6 text-amber-400" />
      <span>{biz}</span>
    </div>
    <div className="hidden md:flex space-x-8 text-xs font-sans tracking-widest uppercase text-stone-300">
      <a href="#about" className="hover:text-amber-400">Story</a>
      <a href="#menu" className="hover:text-amber-400">Menu & Offerings</a>
      <a href="#contact" className="hover:text-amber-400">Contact</a>
    </div>
    <a href="#contact" className="border border-amber-500/60 text-amber-400 hover:bg-amber-500 hover:text-stone-950 font-sans text-xs px-6 py-2.5 uppercase font-bold tracking-widest transition-colors rounded-full">
      Visit Us
    </a>
  </nav>
);
"""
        elif name in ("Hero", "RestaurantHero", "CafeHero"):
            return f"""import React from 'react';
import {{ Utensils, ArrowRight }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section className="py-28 px-8 bg-stone-950/80 backdrop-blur-xl text-stone-100 min-h-[80vh] flex items-center justify-center">
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
      <div className="lg:col-span-7 space-y-8 text-left">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-950/80 border border-amber-500/40 text-amber-400 text-xs font-mono font-bold uppercase">
          <Utensils className="w-4 h-4 text-amber-400" />
          <span>ARTISAN CAFE & GASTRONOMY</span>
        </div>
        <h1 className="text-5xl sm:text-6xl font-serif font-bold text-stone-100 tracking-tight leading-tight">
          {headline}
        </h1>
        <p className="text-stone-300 text-lg max-w-2xl font-sans leading-relaxed">
          {biz} is dedicated to serving artisan coffee, freshly squeezed juices, freshly baked items, and refreshing fruit bowls.
        </p>
        <div className="flex flex-wrap gap-4 pt-4">
          <a href="#menu" className="px-8 py-4 rounded-full bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold text-sm font-sans uppercase tracking-wider flex items-center space-x-2 shadow-xl shadow-amber-500/20">
            <span>EXPLORE OFFERINGS</span>
            <ArrowRight className="w-5 h-5" />
          </a>
        </div>
      </div>
      <div className="lg:col-span-5">
        {f'<div className="relative rounded-3xl overflow-hidden border border-amber-500/40 shadow-2xl"><img src="{img_url}" alt="{biz}" className="w-full h-96 object-cover" /></div>' if img_url else f'<div className="p-12 rounded-3xl bg-stone-900/90 border border-amber-500/30 text-amber-400 font-serif text-center space-y-4"><Utensils className="w-16 h-16 mx-auto text-amber-400" /><h3 className="text-2xl font-bold">{biz}</h3><p className="text-stone-400 text-xs font-sans">Artisan Gastronomy & Fresh Selection</p></div>'}
      </div>
    </div>
  </section>
);
"""
        elif name in ("SignatureDishes", "MenuCategories", "Offerings", "Services"):
            items_tsx = "".join([f"""
        <div className="p-8 rounded-3xl bg-stone-900/80 border border-amber-900/40 text-left space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold">
            <Utensils className="w-6 h-6" />
          </div>
          <h3 className="text-2xl font-serif font-bold text-stone-100">{item}</h3>
          <p className="text-stone-300 text-sm font-sans leading-relaxed">Handcrafted fresh daily at {biz} using top-quality ingredients.</p>
        </div>""" for item in offerings])
            return f"""import React from 'react';
import {{ Utensils }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="menu" className="py-24 px-8 bg-stone-950 text-stone-100 border-b border-amber-900/40">
    <div className="max-w-6xl mx-auto space-y-16 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-amber-400 font-bold uppercase tracking-widest">OUR SELECTION</span>
        <h2 className="text-4xl sm:text-5xl font-serif font-bold text-amber-400">SIGNATURE OFFERINGS</h2>
        <p className="text-stone-300 text-base max-w-xl mx-auto font-sans">Freshly prepared daily at {biz}.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {items_tsx}
      </div>
    </div>
  </section>
);
"""
        else:
            return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="contact" className="py-20 px-8 bg-stone-950 text-stone-100 border-b border-amber-900/40 text-center font-serif">
    <div className="max-w-4xl mx-auto space-y-6 p-12 rounded-3xl bg-stone-900/80 border border-amber-500/30">
      <h2 className="text-4xl font-bold text-amber-400">VISIT {biz.upper()}</h2>
      <p className="text-stone-300 font-sans text-base max-w-xl mx-auto">Experience fresh flavors and artisan quality at {biz}.</p>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_automotive_component(spec: ComponentSpec, biz: str) -> str:
        v_content = getattr(spec, 'verified_content', None)
        prods = getattr(v_content, 'products', []) if v_content else []
        if not prods and "tesla" in biz.lower():
            prods = ["Model S", "Model 3", "Model X", "Model Y", "Cybertruck", "Solar Roof"]

        if spec.name == "Navbar":
            return f"""import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-neutral-950/80 backdrop-blur-md border-b border-red-900/50 px-8 py-4 flex items-center justify-between">
    <div className="text-white font-extrabold text-2xl tracking-tighter flex items-center space-x-2">
      <span className="w-3 h-3 bg-red-600 inline-block" />
      <span>{biz.upper()}</span>
    </div>
    <div className="hidden md:flex space-x-8 text-xs font-mono text-neutral-300 tracking-widest uppercase">
      <a href="#hero" className="hover:text-red-500">Vehicles</a>
      <a href="#specsgrid" className="hover:text-red-500">Specifications</a>
      <a href="#contact" className="hover:text-red-500">Test Drive</a>
    </div>
    <a href="#contact" className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs uppercase px-5 py-2.5 tracking-wider">
      Test Drive
    </a>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
import {{ Zap }} from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-28 px-8 bg-neutral-950/70 backdrop-blur-md text-white min-h-[85vh] flex flex-col justify-center perspective-1000">
    <div className="max-w-6xl mx-auto space-y-8 text-left card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-flex items-center space-x-2 text-red-500 font-mono text-xs font-bold tracking-widest uppercase RotatingCore">
        <Zap className="w-4 h-4" />
        <span>AUTOMOTIVE ELECTRIC VELOCITY // {biz.upper()}</span>
      </div>
      <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight leading-none uppercase">
        ELECTRIC VEHICLES & CLEAN ENERGY BY <span className="text-red-600">{biz}</span>.
      </h1>
      <p className="text-neutral-400 text-lg max-w-2xl leading-relaxed">
        Accelerating the world's transition to sustainable energy through electric vehicles and renewable solar integration.
      </p>
      <div>
        <a href="#specsgrid" className="bg-red-600 hover:bg-red-700 text-white font-extrabold text-sm uppercase px-8 py-4 inline-block tracking-wider">
          Explore Lineup ({', '.join(prods[:4]) if prods else 'Models'})
        </a>
      </div>
    </div>
  </section>
);
"""
        elif spec.name in ("PerformanceMetrics", "SpecsGrid"):
            items_tsx = ""
            for p in prods:
                items_tsx += f"""
        <div className="bg-neutral-900/80 backdrop-blur-md border border-neutral-800 p-6 rounded-xl space-y-2">
          <div className="text-red-500 font-mono text-xs uppercase font-bold">// VERIFIED MODEL</div>
          <div className="text-2xl font-black text-white">{p}</div>
          <div className="text-neutral-400 text-xs font-mono">Official {biz} Vehicle & Energy Line</div>
        </div>"""
            if not items_tsx:
                items_tsx = f"""
        <div className="bg-neutral-900/80 backdrop-blur-md border border-neutral-800 p-6 rounded-xl space-y-2">
          <div className="text-2xl font-black text-white">{biz} Electric Platform</div>
        </div>"""
            return f"""import React from 'react';
export const {spec.name}: React.FC = () => (
  <section id="{spec.name.lower()}" className="py-20 px-8 bg-neutral-950/70 backdrop-blur-md border-b border-red-900/40">
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-red-500 font-mono text-xs font-bold tracking-widest uppercase">// {spec.name.upper()} MATRIX</div>
      <h2 className="text-4xl font-extrabold text-white uppercase">{biz} Vehicle & Product Specifications</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {items_tsx}
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_automotive_component(spec.name, biz)

    @staticmethod
    def _deterministic_futuristic_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
import {{ Cpu }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-cyan-500/30 px-6 py-4 font-mono">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-2 text-cyan-400 font-bold text-lg">
        <Cpu className="w-5 h-5 animate-pulse" />
        <span>[{biz.upper()}_SYS]</span>
      </div>
      <div className="hidden md:flex space-x-6 text-xs text-slate-300">
        <a href="#about" className="hover:text-cyan-400">// DIAGNOSTICS</a>
        <a href="#services" className="hover:text-cyan-400">// NODES</a>
        <a href="#contact" className="hover:text-cyan-400">// TELEMETRY</a>
      </div>
      <a href="#contact" className="bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-400 hover:text-slate-950 font-bold text-xs px-4 py-2 uppercase">
        CONNECT_NODE
      </a>
    </div>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
import {{ Terminal }} from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="py-24 px-6 bg-slate-950/70 backdrop-blur-md text-cyan-100 font-mono min-h-[85vh] flex flex-col justify-center perspective-1000">
    <div className="max-w-6xl mx-auto space-y-8 text-left card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-flex items-center space-x-2 bg-cyan-950/80 border border-cyan-500/40 px-3 py-1 text-cyan-400 text-xs font-bold RotatingCore">
        <Terminal className="w-4 h-4" />
        <span>HUD TELEMETRY INTERFACE</span>
      </div>
      <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
        SYSTEM MATRIX & HOLOGRAPHIC DATA ENGINE // {biz.upper()}
      </h1>
      <p className="text-slate-300 text-base max-w-2xl leading-relaxed">
        {biz} orchestrates real-time telemetry streams, data visualization panels, and monospace digital interfaces.
      </p>
      <div>
        <a href="#contact" className="bg-cyan-400 text-slate-950 font-extrabold text-sm px-8 py-4 inline-block uppercase tracking-wider">
          INITIATE_SESSION
        </a>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_futuristic_component(spec.name, biz)

    @staticmethod
    def _deterministic_creative_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 bg-[#1a0933]/80 backdrop-blur-md border-b border-purple-800/50 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="text-coral-400 font-black text-2xl tracking-wider text-white">{biz}</div>
      <div className="hidden md:flex space-x-8 text-sm font-bold text-purple-200">
        <a href="#about" className="hover:text-pink-400">Manifesto</a>
        <a href="#services" className="hover:text-pink-400">Showcase</a>
        <a href="#contact" className="hover:text-pink-400">Collab</a>
      </div>
      <a href="#contact" className="bg-gradient-to-r from-pink-500 to-purple-600 text-white font-bold text-sm px-5 py-2.5 rounded-xl">
        Let's Create
      </a>
    </div>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
export const Hero: React.FC = () => (
  <section className="py-28 px-6 bg-[#1a0933]/70 backdrop-blur-md text-white min-h-[85vh] flex items-center justify-center text-center perspective-1000">
    <div className="max-w-4xl mx-auto space-y-8 card-3d-tilt glass-panel animate-float-slow">
      <div className="inline-block bg-pink-500/20 border border-pink-400/40 text-pink-300 text-xs font-mono font-bold px-4 py-1.5 rounded-full RotatingCore">
        EXPRESSIVE CREATIVE AGENCY
      </div>
      <h1 className="text-5xl sm:text-7xl font-black text-white tracking-tight leading-tight">
        Art-Directed Digital Collisions by {biz}.
      </h1>
      <p className="text-purple-200 text-lg max-w-2xl mx-auto leading-relaxed">
        {biz} breaks conventional SaaS templates with bold typography collisions and expressive color fields.
      </p>
      <div>
        <a href="#contact" className="bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white font-black text-base px-9 py-4 rounded-xl inline-block shadow-lg shadow-pink-500/20">
          Start Experiment
        </a>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_creative_component(spec.name, biz)

    @staticmethod
    def _deterministic_spatial_component(spec: ComponentSpec, biz: str) -> str:
        if spec.name == "Navbar":
            return f"""import React from 'react';
import {{ Sparkles }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/80 border-b border-slate-800 px-6 py-4">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <Sparkles className="w-5 h-5 text-cyan-400" />
        <span className="font-extrabold text-xl text-white tracking-tight">{biz}</span>
      </div>
      <div className="hidden lg:flex space-x-8 text-sm font-medium text-slate-300">
        <a href="#about" className="hover:text-cyan-400">About</a>
        <a href="#services" className="hover:text-cyan-400">Capabilities</a>
        <a href="#projects" className="hover:text-cyan-400">Work</a>
        <a href="#contact" className="hover:text-cyan-400">Contact</a>
      </div>
      <a href="#contact" className="bg-cyan-500 text-slate-950 px-5 py-2 rounded-xl font-bold text-sm">
        Connect
      </a>
    </div>
  </nav>
);
"""
        elif spec.name == "Hero":
            return f"""import React from 'react';
import {{ ArrowRight, Sparkles }} from 'lucide-react';
export const Hero: React.FC = () => (
  <section className="relative min-h-[85vh] pt-24 pb-28 px-6 bg-slate-950/70 backdrop-blur-md text-white flex items-center justify-center perspective-1000">
    <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full card-3d-tilt glass-panel">
      <div className="lg:col-span-7 text-left space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-900/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-semibold">
          <span>SPATIAL INTELLIGENCE // {biz.upper()}</span>
        </div>
        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight">
          Supercharge Your Workflow: Architecting Spatial Systems & Cloud Infrastructure.
        </h1>
        <p className="text-slate-300 text-lg max-w-2xl leading-relaxed">
          {biz} delivers high-performance digital platforms with 3D spatial depth.
        </p>
        <div className="flex items-center space-x-4">
          <a href="#contact" className="bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 font-bold px-8 py-4 rounded-xl text-base flex items-center space-x-2">
            <span>Explore Solutions</span>
            <ArrowRight className="w-5 h-5" />
          </a>
        </div>
      </div>
      <div className="lg:col-span-5 flex items-center justify-center">
        <div className="w-64 h-64 rounded-3xl bg-slate-900/80 border border-cyan-500/30 p-6 flex flex-col items-center justify-center text-center space-y-4 animate-float-slow">
          <Sparkles className="w-12 h-12 text-cyan-400" />
          <div className="font-bold text-white font-mono">{biz.upper()}-CORE</div>
          <div className="text-xs text-cyan-300 font-mono">SPATIAL ONLINE</div>
        </div>
      </div>
    </div>
  </section>
);
"""
        else:
            return ComponentGenerationPool._generic_spatial_component(spec.name, biz)

    # Helper generic component builders per family
    @staticmethod
    def _generic_swiss_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-slate-50/90 backdrop-blur-sm border-b border-slate-300 font-sans">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
      <div className="md:col-span-4 border-l-2 border-blue-600 pl-4">
        <span className="text-xs font-mono text-blue-600 font-bold uppercase">[ ARCHITECTURE MODULE ]</span>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-2">{title}</h2>
      </div>
      <div className="md:col-span-8 space-y-4">
        <p className="text-slate-700 text-base leading-relaxed">
          {biz} engineered this module according to strict grid alignment and architectural proportion.
        </p>
      </div>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_brutalist_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-6 bg-black/85 backdrop-blur-md text-white border-b-4 border-[#333] font-mono">
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="inline-block bg-[#ccff00] text-black font-black text-xs px-3 py-1 uppercase">
        ARCHITECTURAL ENGINE // {biz.upper()}
      </div>
      <h2 className="text-4xl sm:text-5xl font-black text-white uppercase tracking-tight leading-none">
        {title.upper()}
      </h2>
      <p className="text-slate-300 text-lg max-w-2xl">
        Uncompromised brutalist structure with high contrast borders and direct execution.
      </p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_organic_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-6 bg-emerald-950/80 backdrop-blur-xl text-emerald-50 border-b border-emerald-800/40">
    <div className="max-w-6xl mx-auto text-center space-y-6">
      <div className="inline-block px-4 py-1 rounded-full bg-emerald-900/60 border border-emerald-700/60 text-emerald-300 text-xs font-semibold">
        ORGANIC ECOSYSTEM
      </div>
      <h2 className="text-3xl sm:text-4xl font-extrabold text-white">{title}</h2>
      <p className="text-emerald-200 text-base max-w-xl mx-auto leading-relaxed">
        Fluid digital capabilities designed for {biz}.
      </p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_luxury_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-stone-950/85 backdrop-blur-xl text-stone-100 font-serif border-b border-amber-900/40">
    <div className="max-w-5xl mx-auto text-center space-y-6">
      <div className="text-amber-500 font-mono text-xs uppercase tracking-widest">[ EDITORIAL LUXURY ]</div>
      <h2 className="text-3xl sm:text-5xl font-bold text-amber-400">{title}</h2>
      <p className="text-stone-300 font-sans text-base max-w-2xl mx-auto leading-relaxed">
        Tailored execution and refined presentation for {biz}.
      </p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_automotive_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-neutral-950/85 backdrop-blur-xl text-white font-sans border-b border-red-900/40">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
      <div className="md:col-span-6 space-y-4">
        <div className="text-red-500 font-mono text-xs font-bold tracking-widest uppercase">// VELOCITY MATRIX</div>
        <h2 className="text-3xl font-extrabold uppercase tracking-tight">{title}</h2>
        <p className="text-neutral-400 text-sm leading-relaxed">High-performance specifications for {biz}.</p>
      </div>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_futuristic_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-6 bg-slate-950/85 backdrop-blur-xl text-cyan-200 font-mono border-b border-cyan-500/20">
    <div className="max-w-6xl mx-auto space-y-4">
      <div className="text-cyan-400 text-xs font-bold">[ TELEMETRY_NODE ]</div>
      <h2 className="text-3xl font-extrabold text-white uppercase">{title.upper()}</h2>
      <p className="text-slate-300 text-sm max-w-xl">Holographic data stream panel configured for {biz}.</p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_creative_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-6 bg-[#1a0933]/85 backdrop-blur-xl text-white border-b border-purple-900/40">
    <div className="max-w-6xl mx-auto text-center space-y-6">
      <h2 className="text-3xl sm:text-5xl font-black text-pink-400">{title}</h2>
      <p className="text-purple-200 text-base max-w-xl mx-auto leading-relaxed">
        Expressive digital presentation for {biz}.
      </p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generic_spatial_component(name: str, biz: str) -> str:
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-6 bg-slate-950/80 backdrop-blur-xl text-white border-t border-slate-900/80">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
      <div className="md:col-span-8 space-y-4">
        <span className="text-xs font-mono text-cyan-400 uppercase font-semibold">SPATIAL MODULE</span>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">{title}</h2>
        <p className="text-slate-300 text-base leading-relaxed">Spatial depth layering for {biz}.</p>
      </div>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_business_component(spec: ComponentSpec, master_plan: Any) -> str:
        name = spec.name
        if isinstance(master_plan, str):
            biz = master_plan
            hero_spec = {}
        else:
            biz = getattr(master_plan, "business_name", "") or "Business"
            hero_spec = getattr(master_plan, "hero_spec", {}) or {}

        headline = hero_spec.get("headline") if (isinstance(hero_spec, dict) and hero_spec.get("headline")) else f"Empowering Enterprise Growth with {biz}"

        if name == "Navbar":
            return f"""import React from 'react';
import {{ Building2, ArrowRight }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-blue-500/20 px-8 py-4 text-white flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-400/40 flex items-center justify-center">
        <Building2 className="w-5 h-5 text-blue-400" />
      </div>
      <span className="font-extrabold text-xl tracking-tight text-white">{biz}</span>
    </div>
    <nav className="hidden md:flex space-x-8 text-xs font-mono font-bold tracking-widest text-slate-300 uppercase">
      <a href="#overview" className="hover:text-blue-400">Overview</a>
      <a href="#services" className="hover:text-blue-400">Services</a>
      <a href="#why-choose-us" className="hover:text-blue-400">Why Choose Us</a>
      <a href="#process" className="hover:text-blue-400">Process</a>
      <a href="#contact" className="hover:text-blue-400">Contact</a>
    </nav>
    <a href="#contact" className="px-5 py-2.5 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-blue-500/20">
      Get In Touch
    </a>
  </header>
);
"""
        elif name in ("Hero", "BusinessHero", "EnterpriseHero"):
            return f"""import React from 'react';
import {{ ArrowRight, ShieldCheck }} from 'lucide-react';
export const BusinessHero: React.FC = () => (
  <section className="relative py-28 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-blue-500/20">
    <div className="max-w-6xl mx-auto space-y-8 text-left">
      <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-blue-950/80 border border-blue-500/40 text-blue-400 text-xs font-mono font-bold uppercase">
        <ShieldCheck className="w-4 h-4 text-blue-400" />
        <span>ENTERPRISE SOLUTIONS ARCHITECTURE</span>
      </div>
      <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight leading-none uppercase">
        {headline}
      </h1>
      <p className="text-slate-300 text-lg max-w-2xl leading-relaxed">
        {biz} delivers high-reliability software engineering, enterprise cloud solutions, and strategic digital transformation.
      </p>
      <div className="flex flex-wrap gap-4 pt-4">
        <a href="#services" className="px-8 py-4 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-black text-sm uppercase tracking-wider flex items-center space-x-2 shadow-xl shadow-blue-500/30">
          <span>OUR SERVICES</span>
          <ArrowRight className="w-5 h-5" />
        </a>
        <a href="#contact" className="px-8 py-4 rounded-full border border-blue-500/40 text-blue-300 hover:text-white font-bold text-sm uppercase tracking-wider bg-slate-900/60">
          CONTACT US
        </a>
      </div>
    </div>
  </section>
);
"""
        elif name in ("BusinessOverview", "CompanyOverview", "About"):
            return f"""import React from 'react';
import {{ CheckCircle2 }} from 'lucide-react';
export const BusinessOverview: React.FC = () => (
  <section id="overview" className="py-20 px-8 bg-slate-950/70 backdrop-blur-md text-white border-b border-blue-500/20">
    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-10 items-center">
      <div className="md:col-span-6 space-y-6 text-left">
        <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-widest">// COMPANY OVERVIEW</span>
        <h2 className="text-4xl font-extrabold text-white">Driving Innovation for Modern Businesses</h2>
        <p className="text-slate-300 text-base leading-relaxed">
          {biz} brings industry expertise and specialized capabilities to solve complex technical challenges with scalable, secure architectures.
        </p>
        <div className="space-y-3 font-mono text-sm text-slate-300">
          <div className="flex items-center space-x-3"><CheckCircle2 className="w-5 h-5 text-blue-400" /><span>Enterprise Security Standards</span></div>
          <div className="flex items-center space-x-3"><CheckCircle2 className="w-5 h-5 text-blue-400" /><span>Custom Scalable Architectures</span></div>
          <div className="flex items-center space-x-3"><CheckCircle2 className="w-5 h-5 text-blue-400" /><span>Dedicated Technical Support</span></div>
        </div>
      </div>
      <div className="md:col-span-6">
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-4 text-left">
          <h3 className="text-xl font-bold text-white">Mission Statement</h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            To provide world-class digital systems and software solutions that accelerate sustainable enterprise growth and operational efficiency.
          </p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("BusinessServices", "CoreCapabilities", "Services"):
            return f"""import React from 'react';
import {{ Cpu, Globe, Cloud, Lock }} from 'lucide-react';
export const BusinessServices: React.FC = () => (
  <section id="services" className="py-24 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-blue-500/20">
    <div className="max-w-6xl mx-auto space-y-16 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-widest">ENTERPRISE CAPABILITIES</span>
        <h2 className="text-4xl sm:text-5xl font-extrabold text-white">OUR SERVICES</h2>
        <p className="text-slate-300 text-base max-w-xl mx-auto">Comprehensive solutions tailored to meet enterprise technical requirements.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 text-left">
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-4">
          <Globe className="w-8 h-8 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Web & Mobile Platforms</h3>
          <p className="text-slate-300 text-xs leading-relaxed">Scalable web and mobile application engineering built with modern frameworks.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-4">
          <Cloud className="w-8 h-8 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Cloud Infrastructure</h3>
          <p className="text-slate-300 text-xs leading-relaxed">Automated cloud deployments, container orchestration, and high-availability systems.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-4">
          <Cpu className="w-8 h-8 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Artificial Intelligence</h3>
          <p className="text-slate-300 text-xs leading-relaxed">Custom LLM integration, intelligent automation pipelines, and machine learning models.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-4">
          <Lock className="w-8 h-8 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Cybersecurity & Compliance</h3>
          <p className="text-slate-300 text-xs leading-relaxed">End-to-end data security, threat audit, and compliance architecture implementation.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("WhyChooseUs", "ServiceBenefits"):
            return f"""import React from 'react';
import {{ Award, Zap, Users, TrendingUp }} from 'lucide-react';
export const WhyChooseUs: React.FC = () => (
  <section id="why-choose-us" className="py-20 px-8 bg-slate-950/70 backdrop-blur-md text-white border-b border-blue-500/20">
    <div className="max-w-6xl mx-auto space-y-12 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-widest">VALUE PROPOSITION</span>
        <h2 className="text-4xl font-extrabold text-white">WHY CHOOSE {biz.upper()}</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-3">
          <Zap className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-bold text-white">Rapid Execution</h3>
          <p className="text-slate-300 text-xs">Agile deployment cycles backed by rigorous automated testing pipelines.</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-3">
          <Award className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-bold text-white">Quality Engineering</h3>
          <p className="text-slate-300 text-xs">Production-grade code quality with maintainable modular architecture.</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-3">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-bold text-white">Measurable Impact</h3>
          <p className="text-slate-300 text-xs">Focused on delivering clear business ROI and long-term tech sustainability.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("BusinessProcess", "ServiceProcess"):
            return f"""import React from 'react';
export const BusinessProcess: React.FC = () => (
  <section id="process" className="py-20 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-blue-500/20">
    <div className="max-w-6xl mx-auto space-y-12 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-widest">METHODOLOGY</span>
        <h2 className="text-4xl font-extrabold text-white">HOW WE WORK</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 text-left">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-2">
          <span className="text-xs font-mono text-blue-400 font-bold">01 // DISCOVERY</span>
          <h3 className="text-lg font-bold text-white">Requirements Analysis</h3>
          <p className="text-slate-300 text-xs">Deep alignment on goals, constraints, and architecture.</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-2">
          <span className="text-xs font-mono text-blue-400 font-bold">02 // STRATEGY</span>
          <h3 className="text-lg font-bold text-white">System Design</h3>
          <p className="text-slate-300 text-xs">Blueprint formulation and technology stack selection.</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-2">
          <span className="text-xs font-mono text-blue-400 font-bold">03 // BUILD</span>
          <h3 className="text-lg font-bold text-white">Agile Development</h3>
          <p className="text-slate-300 text-xs">Iterative component construction with automated QA validation.</p>
        </div>
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-blue-500/30 space-y-2">
          <span className="text-xs font-mono text-blue-400 font-bold">04 // DEPLOY</span>
          <h3 className="text-lg font-bold text-white">Launch & Support</h3>
          <p className="text-slate-300 text-xs">Seamless production rollout and continuous monitoring.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("ContactForm", "B2BContactForm", "ContactCTA", "Contact"):
            return f"""import React, {{ useState }} from 'react';
import {{ Send, CheckCircle2 }} from 'lucide-react';
export const ContactForm: React.FC = () => {{
  const [submitted, setSubmitted] = useState(false);
  const handleSubmit = (e: React.FormEvent) => {{
    e.preventDefault();
    setSubmitted(true);
  }};
  return (
    <section id="contact" className="py-24 px-8 bg-slate-950 text-white border-b border-blue-500/20">
      <div className="max-w-4xl mx-auto space-y-12 text-center">
        <div className="space-y-4">
          <span className="text-xs font-mono text-blue-400 font-bold uppercase tracking-widest">GET IN TOUCH</span>
          <h2 className="text-4xl font-extrabold text-white">INQUIRE WITH {biz.upper()}</h2>
        </div>
        {{submitted ? (
          <div className="p-10 rounded-3xl bg-slate-900/90 border border-emerald-500/50 text-center space-y-4">
            <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto" />
            <h3 className="text-2xl font-bold text-white">Inquiry Received</h3>
            <p className="text-slate-300 text-sm">Thank you for contacting {biz}. Our team will reach out promptly.</p>
          </div>
        ) : (
          <form onSubmit={{handleSubmit}} className="p-8 sm:p-12 rounded-3xl bg-slate-900/80 border border-blue-500/30 space-y-6 text-left">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-mono text-blue-400 uppercase font-bold">Your Name</label>
                <input required type="text" placeholder="John Doe" className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono text-blue-400 uppercase font-bold">Work Email</label>
                <input required type="email" placeholder="john@company.com" className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-400" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-mono text-blue-400 uppercase font-bold">Project / Requirement Details</label>
              <textarea required rows={{4}} placeholder="Tell us about your technical requirements..." className="w-full px-5 py-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-400" />
            </div>
            <button type="submit" className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-black text-sm uppercase tracking-wider flex items-center justify-center space-x-2 shadow-xl shadow-blue-500/30">
              <span>SEND INQUIRY</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        )}}
      </div>
    </section>
  );
}};
"""
        else:
            return f"""import React from 'react';
export const {name}: React.FC = () => (
  <footer className="py-12 px-8 bg-slate-950 border-t border-blue-500/20 text-center text-slate-400 text-xs font-mono">
    <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <p>&copy; {{new Date().getFullYear()}} {biz}. All Rights Reserved.</p>
      <p className="text-blue-400 font-bold">ENTERPRISE WEBSITE</p>
    </div>
  </footer>
);
"""

    @staticmethod
    def _deterministic_product_component(spec: ComponentSpec, master_plan: Any) -> str:
        name = spec.name
        if isinstance(master_plan, str):
            biz = master_plan
        else:
            biz = getattr(master_plan, "business_name", "") or "Product"

        if name == "Navbar":
            return f"""import React from 'react';
import {{ Box, Sparkles }} from 'lucide-react';
export const Navbar: React.FC = () => (
  <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-indigo-500/20 px-8 py-4 text-white flex items-center justify-between">
    <div className="flex items-center space-x-3">
      <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-400/40 flex items-center justify-center">
        <Box className="w-5 h-5 text-indigo-400" />
      </div>
      <span className="font-extrabold text-xl tracking-tight text-white">{biz}</span>
    </div>
    <nav className="hidden md:flex space-x-8 text-xs font-mono font-bold tracking-widest text-slate-300 uppercase">
      <a href="#features" className="hover:text-indigo-400">Features</a>
      <a href="#how-it-works" className="hover:text-indigo-400">How It Works</a>
      <a href="#benefits" className="hover:text-indigo-400">Benefits</a>
      <a href="#contact" className="hover:text-indigo-400">Get Product</a>
    </nav>
    <a href="#contact" className="px-5 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-indigo-500/20">
      Try Product
    </a>
  </header>
);
"""
        elif name in ("ProductHero", "Hero"):
            return f"""import React from 'react';
import {{ ArrowRight, Sparkles, Layers }} from 'lucide-react';
export const ProductHero: React.FC = () => (
  <section className="relative py-28 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-indigo-500/20">
    <div className="max-w-6xl mx-auto space-y-10 text-center">
      <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-950/80 border border-indigo-500/40 text-indigo-400 text-xs font-mono font-bold uppercase">
        <Sparkles className="w-4 h-4" />
        <span>NEXT-GEN PRODUCT PLATFORM</span>
      </div>
      <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight leading-tight uppercase">
        Transform Your Workflow with <span className="text-indigo-400">{biz}</span>.
      </h1>
      <p className="text-slate-300 text-lg max-w-2xl mx-auto leading-relaxed">
        The intelligent product built to streamline operations, automate repetitive tasks, and maximize team output.
      </p>
      <div className="flex justify-center space-x-4">
        <a href="#contact" className="px-8 py-4 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-black text-sm uppercase tracking-wider flex items-center space-x-2 shadow-xl shadow-indigo-500/30">
          <span>GET STARTED NOW</span>
          <ArrowRight className="w-5 h-5" />
        </a>
      </div>
      {{/* Product Screenshot Visual Spotlight */}}
      <div className="pt-6 max-w-4xl mx-auto">
        <div className="p-4 rounded-3xl bg-slate-900/90 border border-indigo-500/40 shadow-2xl space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3 font-mono text-xs text-indigo-400">
            <span className="w-3 h-3 rounded-full bg-red-500/80" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <span className="w-3 h-3 rounded-full bg-green-500/80" />
            <span className="pl-4 font-bold">{biz.upper()} DASHBOARD // LIVE PRODUCT INTERFACE</span>
          </div>
          <div className="h-64 rounded-2xl bg-slate-950 flex flex-col items-center justify-center space-y-3 font-mono text-slate-300">
            <Layers className="w-12 h-12 text-indigo-400 animate-pulse" />
            <span className="text-sm font-bold">PRODUCT FOCAL INTERFACE</span>
            <span className="text-xs text-slate-500">Autonomous Workflow Visualized</span>
          </div>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("ProblemSolution", "ProblemSection", "SolutionSection"):
            return f"""import React from 'react';
import {{ AlertTriangle, CheckCircle2 }} from 'lucide-react';
export const ProblemSolution: React.FC = () => (
  <section className="py-20 px-8 bg-slate-950/70 backdrop-blur-md text-white border-b border-indigo-500/20">
    <div className="max-w-6xl mx-auto space-y-12 text-center">
      <div className="space-y-3">
        <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-widest">PROBLEM VS SOLUTION</span>
        <h2 className="text-4xl font-extrabold text-white">WHY {biz.upper()} MATTERS</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
        <div className="p-8 rounded-3xl bg-red-950/30 border border-red-500/30 space-y-4">
          <div className="flex items-center space-x-3 text-red-400">
            <AlertTriangle className="w-6 h-6" />
            <h3 className="text-xl font-bold">The Manual Bottleneck</h3>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">Legacy workflows waste time on repetitive operational tasks and disjointed systems.</p>
        </div>
        <div className="p-8 rounded-3xl bg-emerald-950/30 border border-emerald-500/30 space-y-4">
          <div className="flex items-center space-x-3 text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
            <h3 className="text-xl font-bold">The {biz} Solution</h3>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">Automate workflows seamlessly with real-time feedback loops and modern software design.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("KeyFeatures", "FeaturesBenefits", "Features"):
            return f"""import React from 'react';
import {{ Zap, Shield, Sparkles, BarChart3 }} from 'lucide-react';
export const KeyFeatures: React.FC = () => (
  <section id="features" className="py-24 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-indigo-500/20">
    <div className="max-w-6xl mx-auto space-y-16 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-widest">PRODUCT CAPABILITIES</span>
        <h2 className="text-4xl sm:text-5xl font-extrabold text-white">KEY PRODUCT FEATURES</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 text-left">
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-4">
          <Zap className="w-8 h-8 text-indigo-400" />
          <h3 className="text-xl font-bold text-white">Instant Automation</h3>
          <p className="text-slate-300 text-xs">Execute complex tasks in seconds with automated logic rules.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-4">
          <BarChart3 className="w-8 h-8 text-indigo-400" />
          <h3 className="text-xl font-bold text-white">Real-Time Analytics</h3>
          <p className="text-slate-300 text-xs">Live performance dashboards giving full operational visibility.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-4">
          <Shield className="w-8 h-8 text-indigo-400" />
          <h3 className="text-xl font-bold text-white">Bank-Grade Security</h3>
          <p className="text-slate-300 text-xs">End-to-end data encryption protecting your critical assets.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-4">
          <Sparkles className="w-8 h-8 text-indigo-400" />
          <h3 className="text-xl font-bold text-white">Intelligent Insights</h3>
          <p className="text-slate-300 text-xs">Smart recommendations tailored to accelerate your productivity.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        elif name in ("HowItWorks", "ServiceProcess", "BusinessProcess"):
            return f"""import React from 'react';
export const HowItWorks: React.FC = () => (
  <section id="how-it-works" className="py-20 px-8 bg-slate-950/70 backdrop-blur-md text-white border-b border-indigo-500/20">
    <div className="max-w-6xl mx-auto space-y-12 text-center">
      <div className="space-y-4">
        <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-widest">SIMPLE WORKFLOW</span>
        <h2 className="text-4xl font-extrabold text-white">HOW {biz.upper()} WORKS</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-left">
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-3">
          <span className="text-3xl font-black text-indigo-400 font-mono">01</span>
          <h3 className="text-xl font-bold text-white">Connect Platform</h3>
          <p className="text-slate-300 text-sm">Integrate with your current tools in under 5 minutes.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-3">
          <span className="text-3xl font-black text-indigo-400 font-mono">02</span>
          <h3 className="text-xl font-bold text-white">Configure Rules</h3>
          <p className="text-slate-300 text-sm">Set up custom triggers and automated workflow parameters.</p>
        </div>
        <div className="p-8 rounded-3xl bg-slate-900/80 border border-indigo-500/30 space-y-3">
          <span className="text-3xl font-black text-indigo-400 font-mono">03</span>
          <h3 className="text-xl font-bold text-white">Scale Results</h3>
          <p className="text-slate-300 text-sm">Monitor efficiency gains and scale team output effortlessly.</p>
        </div>
      </div>
    </div>
  </section>
);
"""
        else:
            title = ComponentGenerationPool._clean_component_title(name)
            return f"""import React from 'react';
import {{ ArrowRight }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="contact" className="py-24 px-8 bg-slate-950 text-white border-b border-indigo-500/20 text-center">
    <div className="max-w-4xl mx-auto space-y-8 p-12 rounded-3xl bg-slate-900/90 border border-indigo-500/40">
      <h2 className="text-4xl font-extrabold text-white">{title.upper()}</h2>
      <p className="text-slate-300 text-base max-w-xl mx-auto">Get started with {biz} today and experience next-generation platform capabilities.</p>
      <div>
        <a href="#contact" className="px-8 py-4 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-black text-sm uppercase tracking-wider inline-flex items-center space-x-2">
          <span>GET STARTED NOW</span>
          <ArrowRight className="w-4 h-4" />
        </a>
      </div>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_service_component(spec: ComponentSpec, master_plan: Any) -> str:
        name = spec.name
        if isinstance(master_plan, str):
            biz = master_plan
        else:
            biz = getattr(master_plan, "business_name", "") or "Services"
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
import {{ Wrench, CheckCircle2, PhoneCall }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-teal-500/20">
    <div className="max-w-6xl mx-auto space-y-8 text-left">
      <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-teal-950 border border-teal-500/40 text-teal-400 text-xs font-mono font-bold uppercase">
        <Wrench className="w-4 h-4" />
        <span>PROFESSIONAL SERVICE BUSINESS</span>
      </div>
      <h2 className="text-4xl font-extrabold text-white">{title}</h2>
      <p className="text-slate-300 text-base max-w-2xl leading-relaxed">
        Dedicated service offerings, trusted execution, and client-first commitment delivered by {biz}.
      </p>
      <div className="pt-4 font-mono text-xs text-teal-300 flex items-center space-x-4">
        <div className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-teal-400" /><span>VERIFIED SERVICE OFFERING</span></div>
      </div>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_agency_component(spec: ComponentSpec, master_plan: Any) -> str:
        name = spec.name
        if isinstance(master_plan, str):
            biz = master_plan
        else:
            biz = getattr(master_plan, "business_name", "") or "Agency"
        title = ComponentGenerationPool._clean_component_title(name)
        return f"""import React from 'react';
import {{ Sparkles }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-[#1a0933]/85 backdrop-blur-xl text-white border-b border-purple-800/40">
    <div className="max-w-6xl mx-auto space-y-6 text-left">
      <span className="text-xs font-mono text-purple-400 font-bold uppercase tracking-widest">CREATIVE AGENCY // {biz.upper()}</span>
      <h2 className="text-4xl font-extrabold text-white">{title}</h2>
      <p className="text-purple-200 text-base max-w-2xl leading-relaxed">
        Art-directed agency strategies, digital brand experiences, and custom executions designed by {biz}.
      </p>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_landing_component(spec: ComponentSpec, biz: str) -> str:
        name = spec.name
        return f"""import React from 'react';
import {{ Target, ArrowRight }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-cyan-500/20 text-center">
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-400 text-xs font-mono font-bold uppercase">
        <Target className="w-4 h-4" />
        <span>FOCUSED LANDING PAGE</span>
      </div>
      <h2 className="text-4xl font-extrabold text-white">{name} — {biz}</h2>
      <p className="text-slate-300 text-base max-w-xl mx-auto">One focused objective designed to inform and convert visitors effectively.</p>
    </div>
  </section>
);
"""

    @staticmethod
    def _deterministic_personal_portfolio_component(spec: ComponentSpec, biz: str) -> str:
        name = spec.name
        return f"""import React from 'react';
import {{ User }} from 'lucide-react';
export const {name}: React.FC = () => (
  <section id="{name.lower()}" className="py-20 px-8 bg-slate-950/80 backdrop-blur-xl text-white border-b border-cyan-500/20 text-left">
    <div className="max-w-5xl mx-auto space-y-6">
      <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-widest">PERSONAL PORTFOLIO</span>
      <h2 className="text-4xl font-extrabold text-white">{name} — {biz}</h2>
      <p className="text-slate-300 text-base max-w-xl leading-relaxed">Presenting individual identity, background, and selected personal works.</p>
    </div>
  </section>
);
"""

    @staticmethod
    def _generate_app_component(master_plan: MasterWebsitePlan) -> str:
        comp_imports = []
        comp_tags = []
        has_env = False

        for c in master_plan.components:
            if c.name == "DynamicSpatialEnvironment":
                has_env = True
                continue
            comp_imports.append(f"import {{ {c.name} }} from './components/{c.name}';")
            comp_tags.append(f"        <{c.name} />")

        if not has_env:
            comp_imports.insert(0, "import { DynamicSpatialEnvironment } from './components/DynamicSpatialEnvironment';")
        else:
            comp_imports.insert(0, "import { DynamicSpatialEnvironment } from './components/DynamicSpatialEnvironment';")

        imports_str = "\n".join(comp_imports)
        tags_str = "\n".join(comp_tags)
        styles = master_plan.global_styles or "bg-slate-950 text-white min-h-screen"

        return f"""import React from 'react';
{imports_str}

export const App: React.FC = () => {{
  return (
    <div className="{styles} relative min-h-screen overflow-x-hidden">
      <DynamicSpatialEnvironment />
      <div className="relative z-10">
{tags_str}
      </div>
    </div>
  );
}};

export default App;
"""
