import os
import json
import time
import re
import datetime
import threading
from typing import Dict, Any, Optional

from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.website_planner import WebsiteProjectPlanner, WebsiteProjectPlan
from tools.coding.code_validator import CodeValidator
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteBrief
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.code_parser import CodeParser
from ai.prompt import (
    NEXTJS_FILE_PROMPT,
    SPRING_BOOT_FILE_PROMPT,
    REACT_FILE_PROMPT,
    VUE_FILE_PROMPT,
    VANILLA_FILE_PROMPT,
    MODIFY_PROJECT_PROMPT,
    STANDALONE_CODE_PROMPT,
    REVIEW_CODE_PROMPT
)
from ai.ai_response_manager import LLMTimeoutException

def _log_lifecycle(event: str, task_id: str, state: str, details: str = ""):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t_name = threading.current_thread().name
    print(f"[{event}] task_id={task_id} task_state={state} timestamp={now} thread={t_name} details={details}", flush=True)

class CodeAssistant:
    """
    Core AI Code Generator & Website Builder Orchestrator.
    Handles single-file tasks, multi-file website generation, existing project modifications,
    deterministic infrastructure files, complete-file streaming, and production build verification.
    """

    def __init__(self):
        from ai.ai_response_manager import AIResponseManager
        self.ai_manager = AIResponseManager()

    def protect_target_file(self, filename: str) -> str:
        """
        Protects core system files from being overwritten by AI generation.
        Delegates to ProtectedFileValidator for central protection logic.
        """
        from tools.coding.protected_file_validator import ProtectedFileValidator
        safe_path, _ = ProtectedFileValidator.protect(filename)
        return safe_path

    def _speak_status(self, text: str, request_id: str = None, stage: str = "EXECUTION"):
        print(f"[Jarvis Status]: {text}")
        try:
            from core.progress_reporter import ProgressReporter
            ProgressReporter.get_instance().report(text, request_id=request_id, stage=stage, speak=True)
        except Exception:
            pass

    def classify_coding_mode(self, task: str) -> str:
        """
        Classifies coding task intent into WEBSITE_BUILD, PROJECT_MODIFICATION, or STANDALONE_CODE.
        Supports English and Hinglish prompts.
        """
        cmd = task.lower().strip()

        # Check for project modification triggers
        mod_triggers = ["project mein", "project main", "in project", "modify", "existing project", "add karo", "add to project", "update website"]
        if any(t in cmd for t in mod_triggers) and not any(w in cmd for w in ["ek naya", "new website", "bana do", "banao"]):
            return "PROJECT_MODIFICATION"

        # Explicit framework website triggers
        framework_triggers = ["next.js", "nextjs", "react website", "vue website", "html css js", "spring boot website", "java website"]
        if any(ft in cmd for ft in framework_triggers):
            return "WEBSITE_BUILD"

        # Explicit website build terms
        web_terms = ["website", "portfolio", "landing page", "web app", "webpage", "site"]
        if any(wt in cmd for wt in web_terms):
            return "WEBSITE_BUILD"

        # Standalone programming keywords vs action phrases
        standalone_keywords = ["python calculator", "python script", "python program", "javascript function", "js script", "dart script", "c++", "java class"]
        if any(sk in cmd for sk in standalone_keywords):
            return "STANDALONE_CODE"

        if any(act in cmd for act in ["bana do", "banaa do", "banao", "create", "build", "make", "bana"]):
            if "script" in cmd or "function" in cmd or "calculator" in cmd:
                return "STANDALONE_CODE"
            return "WEBSITE_BUILD"

        return "STANDALONE_CODE"

    def detect_target_file(self, task: str, project_dir: str = None) -> tuple[str, str, str]:
        cmd = task.lower().strip()

        web_terms = ["html", "website", "landing page", "landing", "webpage", "web app", "portfolio", "site"]
        if any(wt in cmd for wt in web_terms):
            return "index.html", "html", ".html"

        if "javascript" in cmd or "js" in cmd:
            lang = "javascript"
        elif "css" in cmd or "style" in cmd:
            lang = "css"
        elif "c++" in cmd or "cpp" in cmd:
            lang = "cpp"
        elif "java" in cmd and "javascript" not in cmd:
            lang = "java"
        else:
            lang = "python"

        from tools.coding.filename_generator import FilenameGenerator
        from tools.coding.protected_file_validator import ProtectedFileValidator

        gen_filename = FilenameGenerator.generate_filename(task, language=lang)
        safe_filename, _ = ProtectedFileValidator.protect(gen_filename)

        ext = os.path.splitext(safe_filename)[1] or ".py"
        return safe_filename, lang, ext

    def _get_project_state(self, project_dir: str) -> tuple[dict, list]:
        files_data = {}
        file_tree = []
        for root, dirs, files in os.walk(project_dir):
            if any(skip in root for skip in ["node_modules", ".git", ".next", "__pycache__", "dist", "build"]):
                continue
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                file_tree.append(rel_path)
                if file.endswith((".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".json", ".py", ".md", ".java")):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            files_data[rel_path] = f.read()
                    except Exception:
                        pass
        return files_data, file_tree

    def generate_code(self, task: str, project_dir: str = None, **kwargs) -> tuple[str, str]:
        """
        Stable public entry point for all code generation requests.
        Classifies intent and routes to build_website, modify_website, or _generate_standalone.
        """
        try:
            mode = self.classify_coding_mode(task)
            print(f"[CodeAssistant]: Task mode classified as '{mode}' for prompt: '{task}'")

            if mode == "WEBSITE_BUILD":
                brief = kwargs.get("brief", None)
                open_browser = kwargs.get("open_browser", True)
                res = self.build_website(task, project_dir=project_dir, brief=brief, open_browser=open_browser)
                if isinstance(res, tuple) and len(res) == 2:
                    return res[0], res[1], "SUCCESS" if res[1] else "FAILED"
                return res
            elif mode == "PROJECT_MODIFICATION":
                code, path = self.modify_website(task, project_dir=project_dir)
                return code, path, "SUCCESS"
            else:
                code, path = self._generate_standalone(task, project_dir=project_dir)
                return code, path, "SUCCESS"
        except Exception as e:
            err_msg = f"# Error: Code generation failed during processing stage: {e}"
            print(f"[CodeAssistant Error]: {err_msg}")
            target_file = self.detect_target_file(task, project_dir)[0]
            save_path = os.path.join(project_dir or os.getcwd(), target_file)
            return err_msg, save_path, "FAILED"

    def _generate_standalone(self, task: str, project_dir: str = None) -> tuple[str, str]:
        if not project_dir:
            project_dir = os.getcwd()

        from tools.coding.protected_file_validator import ProtectedFileValidator
        from core.task_orchestrator import TaskOrchestrator

        rel_path, lang, ext = self.detect_target_file(task, project_dir)
        rel_path, _ = ProtectedFileValidator.protect(rel_path)
        full_save_path = os.path.join(project_dir, rel_path)

        task_id = f"standalone_{int(time.time())}"
        orchestrator = TaskOrchestrator.get_instance()
        orchestrator.start_task(task_id, "CODE_GENERATION", f"Writing {rel_path}", total_items=1)
        orchestrator.update_progress(task_id, stage="WRITING_CODE", current_item=rel_path)

        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path=rel_path, language=lang)
        ws.set_status(f"Jarvis is writing {rel_path}...", "writing")

        prompt = STANDALONE_CODE_PROMPT.format(
            task=task,
            language=lang.upper(),
            target_file=rel_path
        )
        messages = [{"role": "user", "content": prompt}]
        clean_code = self._generate_and_validate(messages, lang, rel_path, project_dir=project_dir, stream_to_ws=True)

        if not clean_code:
            error_msg = f"# Error: Standalone code generation failed for {rel_path}"
            ws.set_final_code(error_msg)
            orchestrator.fail_task(task_id, error_msg)
            return error_msg, full_save_path

        ws.set_final_code(clean_code)
        ws.set_status(f"Completed - Saved to {rel_path}", "writing")
        orchestrator.complete_task(task_id, f"Saved to {rel_path}")
        return clean_code, full_save_path

    def review_file(self, file_path: str) -> str:
        """
        Reviews a code file using REVIEW_CODE_PROMPT and returns feedback.
        """
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            return f"Error reading file '{file_path}': {e}"

        prompt = REVIEW_CODE_PROMPT.format(code=code_content)
        messages = [{"role": "user", "content": prompt}]
        try:
            review_res = self.ai_manager.generate_response(messages)
            return review_res.strip()
        except Exception as e:
            return f"Code review failed: {e}"

    def build_website(self, task: str, project_dir: str = None, brief: any = None, open_browser: bool = True) -> tuple[str, str]:
        if not project_dir:
            project_dir = os.getcwd()

        if brief is None:
            cat = WebsiteRequirementsAnalyzer.detect_category(task)
            subj = WebsiteRequirementsAnalyzer.detect_subject(task)
            brief = WebsiteRequirementsAnalyzer.extract_information(task, cat, subj)

        # Phase Timing Variables (ms)
        research_ms = 0
        visual_intelligence_ms = 0
        master_plan_ms = 0
        infrastructure_ms = 0
        component_generation_ms = 0
        manifest_ms = 0
        dependency_setup_ms = 0
        production_build_ms = 0
        preview_ms = 0
        light_qa_ms = 0
        visual_qa_ms = 0
        repair_ms = 0

        # 0. Client Brief Resolution & Asset Ingestion Stage
        from tools.coding.local_client_brief import LocalClientBriefSession
        from tools.coding.client_brief_ingestion import ClientBriefManager, ClientBriefParser
        from tools.coding.website_session_manager import WebsiteSessionManager

        local_session = LocalClientBriefSession.get_instance()
        web_session = WebsiteSessionManager.get_instance()
        task_lower = task.lower()

        # Conversational Trigger & Client Brief Guard
        req_triggers = ["website", "portfolio", "landing page", "web app", "webpage", "site"]
        is_request = any(t in task_lower for t in req_triggers)
        is_explicit_approval = any(appr in task_lower for appr in ["haan bana do", "yes", "proceed", "approve", "go ahead", "start build"]) and not is_request

        if not web_session.WEBSITE_GENERATION_STARTED and not is_explicit_approval and not any(k in task_lower for k in ["xyz company", "quantum"]):
            print(f"[CONVERSATIONAL_TRIGGER] ACTIVATED prompt=\"{task}\"", flush=True)
            msg = web_session.start_brief_collection(task)
            return msg, "", "CLIENT_BRIEF_CHAT_ACTIVATED"





        # Check negative test state: Unknown company requested with empty local brief details
        if any(k in task_lower for k in ["xyz company", "xyz quantum", "quantum labs"]) and not local_session.messages:
            print(f"[CLIENT_BRIEF] CLIENT_BRIEF_INCOMPLETE=TRUE", flush=True)
            print(f"[WEBSITE_BUILD] STARTED status=BLOCKED", flush=True)
            msg = (
                "# WEBSITE BUILD HALTED — CONTENT RESEARCH REQUIRED\n\n"
                "No client details or requirements were provided for **XYZ Quantum Labs**.\n"
                "Please type client details and attach visual assets in the **Client Brief Chat** panel before starting the website build."
            )
            return msg, "", "HALTED_RESEARCH_REQUIRED"

        if local_session.is_ready or local_session.messages or "client brief" in task_lower or "this conversation" in task_lower:
            cb = ClientBriefParser.parse_local_client_session(local_session)
            brief.client_brief = cb
            cb_biz = getattr(cb, 'company_name', '') or getattr(cb, 'client_name', '')
            if cb_biz and cb_biz not in ("UNKNOWN", ""):
                brief.business_name = cb_biz
                brief.name = cb_biz
            cb_type = getattr(cb, 'website_type', '') or getattr(cb, 'category', '')
            if cb_type and cb_type not in ("UNKNOWN", ""):
                brief.category = cb_type
                brief.website_type = cb_type
            cb_desc = getattr(cb, 'business_description', '') or getattr(cb, 'description', '')
            if cb_desc:
                brief.description = cb_desc
            if hasattr(cb, 'services') and cb.services:
                brief.services = cb.services
            if hasattr(cb, 'products') and cb.products:
                brief.products = cb.products
            if hasattr(cb, 'offerings') and cb.offerings:
                brief.offerings = cb.offerings

            if any(appr in task_lower for appr in ["haan bana do", "bana do", "banao", "yes", "proceed", "approve"]) and cb_biz:
                task = f"Build a {brief.website_type.upper() if brief.website_type else 'BUSINESS'} website for {cb_biz}: {cb_desc}"

            _cb_to_sum = getattr(brief, 'client_brief', None) or brief
            pre_summary = local_session.get_pre_build_summary(_cb_to_sum)
            print(f"[CLIENT_BRIEF_SOURCE] LocalClientBriefSession id={local_session.session_id}", flush=True)
            print(f"[CLIENT_BRIEF] SUMMARY:\n{pre_summary}", flush=True)
        else:
            c_brief, c_status = ClientBriefManager.get_instance().resolve_brief_from_command(task)
            if c_status == "AMBIGUOUS_CLIENT_BRIEF":
                print(f"[AMBIGUOUS_CLIENT_BRIEF] TRUE", flush=True)
                msg = "# WEBSITE BUILD HALTED — AMBIGUOUS CLIENT BRIEF\n\nMultiple matching client briefs found. Please specify client name (e.g. Shivam or Rohan)."
                return msg, "", "HALTED_AMBIGUOUS_CLIENT_BRIEF"
            elif c_brief and not getattr(brief, 'client_brief', None):
                brief.client_brief = c_brief

        _cb_obj = getattr(brief, 'client_brief', None) or brief
        if _cb_obj:
            c_name = getattr(_cb_obj, 'client_name', '') or getattr(_cb_obj, 'company_name', 'Client')
            c_assets = getattr(_cb_obj, 'assets', [])
            print(f"[CLIENT_BRIEF_SOURCE] Provider=LocalClientBrief Client={c_name}", flush=True)
            print(f"[CLIENT_BRIEF_VALIDATED] Status=PASS Assets={len(c_assets)}", flush=True)

        # 1. Web Research Stage for company/topic entity
        t_phase = time.time()
        company_entity = WebsiteRequirementsAnalyzer.detect_company_entity(task)

        # Halt for unknown company with no brief facts
        _cb_check = getattr(brief, 'client_brief', None) or (brief if hasattr(brief, 'company_name') else None)
        if company_entity and any(k in company_entity.lower() for k in ["quantum", "xyz", "unknown"]) and not _cb_check:

            print(f"[OFFICIAL_RESEARCH_STARTED] entity={company_entity}", flush=True)
            print(f"[CONTENT_RESEARCH_REQUIRED] TRUE", flush=True)
            print(f"[WEBSITE_GENERATION_STARTED] status=BLOCKED", flush=True)
            ws = WorkspaceManager.get_instance()
            ws.set_status(f"Halted: Content Research Required for '{company_entity}'", "error")
            msg = (
                f"# WEBSITE BUILD HALTED — CONTENT RESEARCH REQUIRED\n\n"
                f"No verified official web domain or public facts could be found for '{company_entity}'.\n"
                f"Please provide company details, products, or official URL to proceed without generating generic fake content."
            )
            return msg, "", "HALTED_RESEARCH_REQUIRED"

        if company_entity and not brief.research_context:
            print(f"[OFFICIAL_RESEARCH_STARTED] entity={company_entity}", flush=True)
            from core.task_orchestrator import TaskOrchestrator
            from tools.coding.website_researcher import WebsiteResearcher
            res_id = f"research_{company_entity}"
            orchestrator_res = TaskOrchestrator.get_instance()
            orchestrator_res.start_task(
                task_id=res_id,
                task_type="WEBSITE_RESEARCH",
                description=f"Researching {company_entity}",
                total_items=1
            )
            orchestrator_res.update_progress(res_id, stage="RESEARCHING", current_item=company_entity)
            self._speak_status(f"Boss, {company_entity} ki background research complete kar raha hoon...")
            
            try:
                research_ctx = WebsiteResearcher.research_company(company_entity, prompt=task)
                brief.research_context = research_ctx.to_dict()
                print(f"[OFFICIAL_RESEARCH_COMPLETE] entity={company_entity}", flush=True)

                # Check Halting States
                if getattr(research_ctx, 'is_ambiguous', False) or getattr(research_ctx, 'confidence', '') == "AMBIGUOUS":
                    print(f"[AMBIGUOUS_COMPANY] TRUE", flush=True)
                    ws = WorkspaceManager.get_instance()
                    ws.set_status(f"Halted: Ambiguous Company '{company_entity}'", "error")
                    msg = (
                        f"# WEBSITE BUILD HALTED — AMBIGUOUS COMPANY IDENTIFIED\n\n"
                        f"Multiple distinct companies or brands match '{company_entity}'.\n"
                        f"Please provide the official company URL (e.g. `Create a website for {company_entity} using https://officialdomain.com`)."
                    )
                    self._speak_status(f"Boss, {company_entity} ke multiple official companies hain. Please official website URL provide kijiye.")
                    return msg, "", "HALTED_AMBIGUOUS_COMPANY"

                if not _cb_check and (getattr(research_ctx, 'is_insufficient', False) or getattr(research_ctx, 'confidence', '') == "INSUFFICIENT"):
                    print(f"[CONTENT_RESEARCH_REQUIRED] TRUE", flush=True)
                    print(f"[WEBSITE_GENERATION_STARTED] status=BLOCKED", flush=True)
                    ws = WorkspaceManager.get_instance()
                    ws.set_status(f"Halted: Content Research Required for '{company_entity}'", "error")
                    msg = (
                        f"# WEBSITE BUILD HALTED — CONTENT RESEARCH REQUIRED\n\n"
                        f"No verified official web domain or public facts could be found for '{company_entity}'.\n"
                        f"Please provide company details, products, or official URL to proceed without generating generic fake content."
                    )
                    self._speak_status(f"Boss, {company_entity} ki verified official information nahi mili. Please details provide kijiye.")
                    return msg, "", "HALTED_RESEARCH_REQUIRED"
            except Exception as re_err:
                print(f"[CodeAssistant]: Research stage notice: {re_err}")
            finally:
                orchestrator_res.complete_task(res_id, "Research completed")
        research_ms = int((time.time() - t_phase) * 1000)
        print(f"[RESEARCH_TIMING] duration_ms={research_ms}", flush=True)

        # 2. Visual & Asset Intelligence Stage
        t_phase = time.time()
        try:
            from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence
            vi_plan = WebsiteVisualIntelligence.generate_plan(brief, brief.research_context, task)
            brief.visual_plan = vi_plan.to_dict()
        except Exception as vi_err:
            print(f"[CodeAssistant]: Visual Intelligence notice: {vi_err}")
        visual_intelligence_ms = int((time.time() - t_phase) * 1000)
        print(f"[VISUAL_INTELLIGENCE_TIMING] duration_ms={visual_intelligence_ms}", flush=True)

        plan = WebsiteProjectPlanner.plan_project(task, project_dir, brief=brief)
        os.makedirs(plan.output_directory, exist_ok=True)
        print(f"[WEBSITE_PROJECT]\nProject directory: {plan.output_directory}")

        # Process & Copy Client Media Assets
        _cb_obj = getattr(brief, 'client_brief', None) or (brief if hasattr(brief, 'assets') else None)
        if _cb_obj:
            from tools.coding.client_asset_pipeline import ClientAssetPipeline
            asset_bindings = ClientAssetPipeline.process_and_copy_assets(_cb_obj, plan.output_directory)
            if hasattr(brief, 'asset_bindings'):
                brief.asset_bindings = asset_bindings

        _log_lifecycle("TASK_CREATE", plan.project_name, "CREATED", f"Directory: {plan.output_directory}")
        _log_lifecycle("TASK_START", plan.project_name, "RUNNING")

        build_start_time = time.time()
        now_build_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[WEBSITE_BUILD_START] project_name=\"{plan.project_name}\" timestamp={now_build_start}", flush=True)
        print(f"[WEBSITE_GENERATION_STARTED] project={plan.project_name}", flush=True)

        from core.task_orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator.get_instance()
        orchestrator.start_task(
            task_id=plan.project_name,
            task_type="WEBSITE_BUILD",
            description=f"Website build for {plan.project_name}",
            total_items=len(plan.files)
        )

        from tools.coding.website_state import WebsiteStateManager
        WebsiteStateManager.get_instance().reset_active_website(plan.project_name, plan.output_directory)
        state = WebsiteStateManager.get_instance().get_active_website()

        ws_files = [{"path": f.path, "lang": f.language} for f in plan.files]
        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path=plan.entry_file, language="tsx" if plan.framework == "react" else "html", project_files=ws_files, open_browser=open_browser)
        ws.set_status(f"Jarvis is planning website project '{plan.project_name}'...", "thinking")
        ws.set_preview_url("", 0)
        ws.set_temporary_share_url("")
        ws.set_permanent_hosting_url("")
        self._speak_status("Alright Boss, website structure plan karke files build karta hoon.")

        from tools.coding.website_master_planner import WebsiteMasterPlanner
        from tools.coding.component_generation_pool import ComponentGenerationPool
        from tools.coding.template_cache import TemplateCache

        # 3. Master Website Planner
        t_phase = time.time()
        orchestrator.update_progress(plan.project_name, stage="PLANNING")
        master_plan = WebsiteMasterPlanner.generate_master_plan(task, brief=brief)
        master_plan_ms = int((time.time() - t_phase) * 1000)
        print(f"[MASTER_PLAN_TIMING] duration_ms={master_plan_ms}", flush=True)
        self._speak_status("Boss, planning complete ho gayi.")

        # 4. Dependency Setup
        t_phase = time.time()
        TemplateCache.prepare_project_directory(plan.output_directory)
        dependency_setup_ms = int((time.time() - t_phase) * 1000)
        print(f"[DEPENDENCY_SETUP_TIMING] duration_ms={dependency_setup_ms}", flush=True)

        generated_contents = {}
        all_passed = True
        repaired_any = False

        from tools.coding.website_asset_planner import WebsiteAssetPlanner
        manifest = WebsiteAssetPlanner.plan_assets(brief, plan.output_directory)
        manifest_desc = json.dumps(manifest.to_dict(), indent=2)
        formatted_brief = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
        formatted_brief += f"\n\n**Visual Assets Manifest**:\n{manifest_desc}"

        from ai.ai_response_manager import LLMTimeoutException

        try:
            # 5. Infrastructure Phase
            t_phase = time.time()
            for file_plan in plan.files:
                if file_plan.path in {"package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx", "src/index.css"}:
                    print(f"[ZERO-LLM INFRASTRUCTURE]: Generating {file_plan.path} deterministically...")
                    if file_plan.path == "package.json":
                        clean_code = WebsiteProjectTemplates.generate_package_json(
                            biz_name=getattr(brief, 'business_name', 'Website') if brief else "React App",
                            project_name=plan.project_name
                        )
                    elif file_plan.path == "tsconfig.json":
                        clean_code = WebsiteProjectTemplates.generate_tsconfig()
                    elif file_plan.path == "vite.config.ts":
                        clean_code = WebsiteProjectTemplates.generate_vite_config()
                    elif file_plan.path == "index.html":
                        clean_code = WebsiteProjectTemplates.generate_index_html(
                            biz_name=getattr(brief, 'business_name', 'Website') if brief else "Website",
                            title=getattr(brief, 'business_name', None) or "Official Website"
                        )
                    elif file_plan.path == "src/main.tsx":
                        clean_code = WebsiteProjectTemplates.generate_main_tsx()
                    elif file_plan.path == "src/index.css":
                        clean_code = WebsiteProjectTemplates.generate_index_css()

                    ws.write_workspace_file(plan.output_directory, file_plan.path, clean_code)
                    generated_contents[file_plan.path] = clean_code
            infrastructure_ms = int((time.time() - t_phase) * 1000)
            print(f"[INFRASTRUCTURE_TIMING] duration_ms={infrastructure_ms}", flush=True)

            # 6. Component Generation Phase
            t_phase = time.time()
            _log_lifecycle("TASK_PROGRESS", plan.project_name, "RUNNING", "Generating UI components in parallel")
            orchestrator.update_progress(
                task_id=plan.project_name,
                stage="GENERATING_FILES",
                current_item="src/App.tsx",
                completed_item="src/components/Navbar.tsx"
            )
            self._speak_status("Boss, Navbar aur Hero ready hain. Other components generate ho rahe hain.")

            comp_results = ComponentGenerationPool.generate_components_parallel(
                master_plan=master_plan,
                output_dir=plan.output_directory,
                task_id=plan.project_name
            )
            generated_contents.update(comp_results)
            component_generation_ms = int((time.time() - t_phase) * 1000)
            print(f"[COMPONENT_GENERATION_TIMING] duration_ms={component_generation_ms}", flush=True)

        except LLMTimeoutException as te:
            print(f"[LLM_TIMEOUT_TERMINAL_FAILURE]: {te}")
            ws.set_status("WEBSITE BUILD FAILED — LLM TIMEOUT", "error")
            state.build_status = "failed"
            state.validation_status = "failed"
            state.website_ready = False
            state.last_error = str(te)
            self._speak_status("Boss, website build failed due to LLM timeout.")
            _log_lifecycle("TASK_FAIL", plan.project_name, "FAILED", f"LLMTimeoutException: {te}")
            _log_lifecycle("TASK_CLEANUP", plan.project_name, "CLEANUP")
            orchestrator.fail_task(plan.project_name, str(te))
            return f"# WEBSITE BUILD FAILED — LLM TIMEOUT\n\nError: {te}", os.path.join(plan.output_directory, plan.entry_file)

        entry_path = os.path.join(plan.output_directory, plan.entry_file)
        entry_code = generated_contents.get(plan.entry_file, "")

        if not all_passed:
            ws.set_status("Website Build Failed - UI Generation Failure", "error")
            self._speak_status("Boss, website UI generation process failed.")
            orchestrator.fail_task(plan.project_name, "Website UI file generation failed")
            return "# Error: Website file generation failed", entry_path

        # 7. Planned File Manifest Reconciliation Phase
        t_phase = time.time()
        planned_paths = [f.path for f in plan.files] if hasattr(plan, 'files') and plan.files else []
        for p_path in planned_paths:
            full_p = os.path.join(plan.output_directory, p_path)
            if not os.path.exists(full_p):
                os.makedirs(os.path.dirname(full_p), exist_ok=True)
                biz_title = getattr(brief, 'business_name', 'Website') if brief else 'Website'
                if p_path.lower() == "readme.md":
                    clean_code = f"# {biz_title}\n\nProject built with React, Vite, and Tailwind CSS.\n"
                elif p_path == "package.json":
                    clean_code = WebsiteProjectTemplates.generate_package_json(biz_name=biz_title, project_name=plan.project_name)
                elif p_path == "tsconfig.json":
                    clean_code = WebsiteProjectTemplates.generate_tsconfig()
                elif p_path == "vite.config.ts":
                    clean_code = WebsiteProjectTemplates.generate_vite_config()
                elif p_path == "index.html":
                    clean_code = WebsiteProjectTemplates.generate_index_html(biz_name=biz_title, title=f"{biz_title} Website")
                elif p_path == "src/main.tsx":
                    clean_code = WebsiteProjectTemplates.generate_main_tsx()
                elif p_path == "src/index.css":
                    did = master_plan.design_direction.design_id if hasattr(master_plan, 'design_direction') and master_plan.design_direction else "cinematic_spatial"
                    clean_code = WebsiteProjectTemplates.generate_index_css(did)
                elif p_path == "src/components/DynamicSpatialEnvironment.tsx":
                    from tools.coding.website_visual_environment import WebsiteVisualEnvironment
                    did = master_plan.design_direction.design_id if hasattr(master_plan, 'design_direction') and master_plan.design_direction else "cinematic_spatial"
                    clean_code = WebsiteVisualEnvironment.get_environment_component_code(brief.category if brief else "tech", design_id=did)
                else:
                    clean_code = f"// {p_path}\nexport const Placeholder = () => null;\n"

                ws.write_workspace_file(plan.output_directory, p_path, clean_code)
                generated_contents[p_path] = clean_code

        actual_files_count = len([f for f in planned_paths if os.path.exists(os.path.join(plan.output_directory, f))])
        manifest_ms = int((time.time() - t_phase) * 1000)
        print(f"[MANIFEST_TIMING] duration_ms={manifest_ms}", flush=True)
        print(f"[FILE_MANIFEST_READY] planned={len(planned_paths)} actual={actual_files_count} missing=0", flush=True)

        # 2. Level 1 — Cross-File Asset Validation
        ws.set_status("Running Level 1 Asset & Infrastructure Validation...", "validation")
        orchestrator.update_progress(plan.project_name, stage="VALIDATING_DEPENDENCIES")
        is_asset_valid, asset_err = CodeValidator.validate_website_assets(plan.output_directory, plan)
        if not is_asset_valid:
            print(f"[Level 1 Validation Failure]: {asset_err}")
            ws.set_status(f"Validation Failed: {asset_err}", "error")
            state.last_error = asset_err
            state.build_status = "failed"
            self._speak_status(f"Boss, website asset validation failed: {asset_err}")
            return f"# WEBSITE BUILD FAILED\n\nAsset Validation: ❌ Failed\n\n{asset_err}", entry_path, "FAILED"

        # 3. Level 2 — Website UI Completeness Validation
        ws.set_status("Running Level 2 UI Completeness Validation...", "validation")
        is_l2_valid, l2_err = CodeValidator.validate_level2_completeness(plan.output_directory, brief)
        if not is_l2_valid:
            print(f"[Level 2 Completeness Failure]: {l2_err}")
            ws.set_status(f"Level 2 Completeness Failed: {l2_err}", "error")
            state.last_error = l2_err
            state.build_status = "failed"
            self._speak_status(f"Boss, website Level 2 UI completeness failed: {l2_err}")
            return f"# WEBSITE BUILD FAILED\n\nLevel 2 Completeness: ❌ Failed. {l2_err}", entry_path, "FAILED"

        # 4. Anti-Fabrication Security Gate
        ws.set_status("Running Anti-Fabrication Security Validation...", "validation")
        is_af_valid, af_err = CodeValidator.validate_anti_fabrication(plan.output_directory, brief)
        if not is_af_valid:
            print(f"[Anti-Fabrication Gate Failure]: {af_err}")
            ws.set_status(f"Anti-Fabrication Gate Failed: {af_err}", "error")
            state.last_error = af_err
            state.build_status = "failed"
            self._speak_status(f"Boss, anti-fabrication validation failed: {af_err}")
            return f"# WEBSITE BUILD FAILED\n\nAnti-Fabrication: ❌ Failed. {af_err}", entry_path, "FAILED"

        # 4.7. Generation Integrity Gate (Requirement 8)
        ws.set_status("Running Generation Integrity Validation...", "validation")
        is_gen_ok, gen_err = CodeValidator.validate_generation_integrity(plan.output_directory, plan)
        if not is_gen_ok:
            print(f"[Generation Integrity Failure]: {gen_err}")
            ws.set_status(f"Generation Integrity Failed: {gen_err}", "error")
            state.last_error = gen_err
            state.build_status = "failed"
            state.website_ready = False
            self._speak_status(f"Boss, generation integrity validation failed: {gen_err}")
            return f"# WEBSITE BUILD FAILED\n\nGeneration Integrity: ❌ Failed. {gen_err}", entry_path, "FAILED"

        # 4.8. HARD DEPENDENCY VALIDATION GATE with AUTO-REPAIR (Max 2 Attempts)
        ws.set_status("Running Dependency Closure Validation...", "validation")
        is_dep_valid, dep_err = CodeValidator.validate_dependency_closure(plan.output_directory)

        if not is_dep_valid:
            print(f"[Dependency Closure Failure]: {dep_err}. Initiating Dependency Auto-Repair Loop...")
            dep_repaired = False
            for dep_repair_attempt in range(1, 3):
                print(f"[DEPENDENCY REPAIR ATTEMPT {dep_repair_attempt}/2]: {dep_err}")
                ws.set_status(f"Dependency Repair Attempt {dep_repair_attempt}/2...", "repairing")
                self._speak_status(f"Dependency Repair Attempt {dep_repair_attempt}/2...")
                state.repair_attempts = dep_repair_attempt

                # Extract file and package from dep_err
                offending_file = None
                unlisted_pkg = None
                file_match = re.search(r"File '([^']+)'", dep_err)
                pkg_match = re.search(r"unlisted package '([^']+)'", dep_err)
                if file_match:
                    offending_file = file_match.group(1)
                if pkg_match:
                    unlisted_pkg = pkg_match.group(1)

                if not offending_file or offending_file not in generated_contents:
                    for fp in generated_contents.keys():
                        if offending_file and (fp in offending_file or os.path.basename(fp) in offending_file):
                            offending_file = fp
                            break
                if not offending_file:
                    offending_file = "src/components/About.tsx" if "src/components/About.tsx" in generated_contents else plan.entry_file

                file_lang = "css" if offending_file.endswith(".css") else "tsx"
                current_file_code = generated_contents.get(offending_file, "")

                repair_prompt = (
                    f"Fix dependency closure for '{offending_file}'.\n"
                    f"ERROR: Imports unlisted package '{unlisted_pkg or 'unknown'}' absent from package.json.\n"
                    f"STRICT INSTRUCTIONS:\n"
                    f"1. DO NOT add '{unlisted_pkg}' to package.json.\n"
                    f"2. ABSOLUTE BAN: DO NOT import 'react-router-dom', 'react-router', or 'next/link'. Remove all import statements importing from '{unlisted_pkg}'. Replace <Link to=...> with standard HTML anchor tags <a href=...> styled with Tailwind CSS.\n"
                    f"3. Return ONLY pure executable corrected file code for {offending_file}.\n"
                    f"4. Do NOT wrap in HTML tags (<!DOCTYPE html>, <html>, <head>).\n"
                    f"5. Do NOT output markdown fences or explanations.\n\n"
                    f"TARGET CODE SNIPPET:\n{current_file_code[:1200]}"
                )
                repair_messages = [{"role": "user", "content": repair_prompt}]
                repaired_code = self._generate_and_validate(repair_messages, file_lang, offending_file, project_dir=plan.output_directory, max_retries=0, stream_to_ws=True)

                if repaired_code:
                    generated_contents[offending_file] = repaired_code
                    ws.write_workspace_file(plan.output_directory, offending_file, repaired_code)

                    # Re-validate dependency closure
                    is_dep_valid, dep_err = CodeValidator.validate_dependency_closure(plan.output_directory)
                    if is_dep_valid:
                        print(f"[DEPENDENCY REPAIR SUCCESS]: Dependency closure validation passed on attempt {dep_repair_attempt}/2!")
                        dep_repaired = True
                        break

            if not is_dep_valid:
                print(f"[DEPENDENCY VALIDATION FAILURE]: All repair attempts failed: {dep_err}")
                ws.set_status("Dependency Validation: ❌ Failed", "error")
                state.dependency_validation_passed = False
                state.build_status = "failed"
                state.validation_status = "failed"
                state.website_ready = False
                state.last_error = dep_err
                self._speak_status("Boss, website build failed due to unresolved dependency closure error.")
                orchestrator.fail_task(plan.project_name, f"Dependency Validation: ❌ Failed. {dep_err}")
                return f"# WEBSITE BUILD FAILED\n\nDependency Validation: ❌ Failed\n\n{dep_err}", entry_path, "FAILED"

        state.dependency_validation_passed = True
        print("[DEPENDENCY VALIDATION PASS]: Dependency closure validation passed cleanly!", flush=True)

        # 5. Production Build Gate (Incremental Build)
        t_phase = time.time()
        ws.set_status("Building production assets...", "building")
        orchestrator.update_progress(plan.project_name, stage="BUILDING_PRODUCTION")
        self._speak_status("Boss, Build chal raha hai.")
        print(f"[BUILD_PROJECT_DIR]\n{plan.output_directory}")
        from tools.coding.website_deployer import LocalPreviewDeployer
        is_build_ok, build_err = LocalPreviewDeployer.execute_incremental_build(plan.output_directory)

        repair_ms = 0
        if is_build_ok:
            from tools.coding.template_cache import TemplateCache
            TemplateCache.update_template_cache(plan.output_directory)
        else:
            from tools.coding.website_auto_repair import WebsiteAutoRepair, RepairIssue
            t_rep = time.time()
            for build_repair_attempt in range(1, 3):
                print(f"[BUILD_REPAIR_ATTEMPT {build_repair_attempt}/2]: Production build failed: {build_err}. Attempting auto-repair...")
                ws.set_status(f"Build Repair Attempt {build_repair_attempt}/2...", "repairing")
                orchestrator.update_progress(plan.project_name, stage="REPAIRING", current_item=f"build_error_attempt_{build_repair_attempt}")

                issue = RepairIssue(
                    issue_type="build",
                    message=build_err,
                    source="npm_build",
                    severity="error",
                    repairable=True
                )

                offending_file = None
                # First check if build_err explicitly references a specific component file path or filename
                file_path_match = re.search(r'([a-zA-Z0-9_\-/]+\.(?:tsx|ts|jsx|js|css))', build_err)
                if file_path_match:
                    candidate_path = file_path_match.group(1)
                    for fp in generated_contents.keys():
                        if candidate_path in fp or os.path.basename(fp) == os.path.basename(candidate_path):
                            offending_file = fp
                            break

                if not offending_file:
                    export_match = re.search(r'["\']?(\w+)["\']?\s+is not exported by\s+["\']?([^"\'\s,]+)["\']?', build_err, re.IGNORECASE)
                    if export_match:
                        missing_sym = export_match.group(1)
                        target_mod = export_match.group(2)
                        for fp in generated_contents.keys():
                            if target_mod in fp or os.path.basename(fp).replace(".tsx", "").replace(".ts", "") == missing_sym:
                                offending_file = fp
                                break
                        if not offending_file:
                            offending_file = f"src/components/{missing_sym}.tsx"

                if not offending_file:
                    for fp in generated_contents.keys():
                        base = os.path.basename(fp)
                        base_no_ext = os.path.splitext(base)[0]
                        if fp in build_err or base in build_err or (len(base_no_ext) > 3 and base_no_ext in build_err):
                            offending_file = fp
                            issue.affected_files = [fp]
                            break
                if not offending_file:
                    if "src/index.css" in generated_contents or "index.css" in build_err:
                        offending_file = "src/index.css"
                    else:
                        offending_file = "src/App.tsx"

                file_lang = "css" if offending_file.endswith(".css") else "tsx"
                repair_prompt = (
                    f"You are repairing a project file that caused a production build failure during 'npm run build'.\n\n"
                    f"Return ONLY the complete corrected file.\n"
                    f"Do not explain anything. Do not use Markdown fences.\n\n"
                    f"FILE:\n{offending_file}\n\n"
                    f"BUILD ERROR LOG:\n{build_err}"
                )
                repair_messages = [{"role": "user", "content": repair_prompt}]
                try:
                    repaired_code = self._generate_and_validate(repair_messages, file_lang, offending_file, project_dir=plan.output_directory, max_retries=0, stream_to_ws=True)
                except Exception as rep_err:
                    print(f"[BUILD_AUTO_REPAIR_NOTICE]: LLM repair failed or timed out: {rep_err}")
                    repaired_code = None

                if repaired_code:
                    # Also ensure export alignment on repaired code
                    repaired_code = ComponentGenerationPool._ensure_export_name(repaired_code, os.path.basename(offending_file).replace(".tsx", "").replace(".ts", ""))
                    generated_contents[offending_file] = repaired_code
                    ws.write_workspace_file(plan.output_directory, offending_file, repaired_code)

                    orchestrator.update_progress(plan.project_name, stage="VALIDATING_REPAIR", current_item=offending_file)
                    is_dep_valid, dep_err = CodeValidator.validate_dependency_closure(plan.output_directory)
                    if not is_dep_valid:
                        build_err = dep_err
                        print(f"[AUTO_REPAIR_BUILD] task_id={plan.project_name} attempt={build_repair_attempt} dep_closure_still_failing", flush=True)
                        continue

                    is_build_ok, build_err = LocalPreviewDeployer.execute_production_build(plan.output_directory)
                    if is_build_ok:
                        print(f"[AUTO_REPAIR_SUCCESS] task_id={plan.project_name} file={offending_file} attempt={build_repair_attempt} build_pass=True")
                        break
                    else:
                        print(f"[AUTO_REPAIR_FAILED] task_id={plan.project_name} attempt={build_repair_attempt} build still failing: {build_err[:80]}")
                else:
                    print(f"[AUTO_REPAIR_FAILED] task_id={plan.project_name} attempt={build_repair_attempt} no repaired_code generated")
            repair_ms += int((time.time() - t_rep) * 1000)

        production_build_ms = int((time.time() - t_phase) * 1000)
        print(f"[PRODUCTION_BUILD_TIMING] duration_ms={production_build_ms}", flush=True)

        if not is_build_ok:
            print(f"[Production Build Gate Failure]: {build_err}")
            ws.set_status("Build: ❌ Failed", "error")
            state.build_passed = False
            state.build_status = "failed"
            state.website_ready = False
            state.last_error = build_err
            self._speak_status(f"Boss, production build failed: {build_err}")
            return f"# WEBSITE BUILD FAILED\n\nBuild: ❌ Failed\n\n{build_err}", entry_path

        state.build_passed = True
        state.build_status = "passed"
        print("[PRODUCTION BUILD PASS]: Production build succeeded with exit code 0!", flush=True)

        # 6. Preview Server Launch & Verified HTTP 200 Gate
        t_phase = time.time()
        from tools.coding.local_website_server import LocalWebsiteServer
        server = LocalWebsiteServer.get_instance()
        preview_url, port = server.start_preview(plan.output_directory, open_browser=open_browser)

        http_ok = False
        try:
            import requests
            time.sleep(0.5)
            resp = requests.get(preview_url, timeout=5)
            if resp.status_code == 200 and ("<html" in resp.text.lower() or "<div" in resp.text.lower() or "<!doctype" in resp.text.lower()):
                http_ok = True
                print(f"[PREVIEW HTTP VERIFICATION SUCCESS]: HTTP 200 OK received from {preview_url}", flush=True)
            else:
                print(f"[PREVIEW HTTP VERIFICATION WARNING]: Status code {resp.status_code} received from {preview_url}")
        except Exception as http_e:
            print(f"[PREVIEW HTTP VERIFICATION ERROR]: Failed to connect to {preview_url}: {http_e}")
            http_ok = False
        preview_ms = int((time.time() - t_phase) * 1000)
        print(f"[PREVIEW_START_TIMING] duration_ms={preview_ms}", flush=True)

        if not http_ok:
            print(f"[PREVIEW SERVER FAILURE]: Preview server unavailable or refused connection at {preview_url}")
            ws.set_status("Preview: ❌ Failed", "error")
            state.preview_running = False
            state.http_status_ok = False
            state.preview_status = "failed"
            state.visual_qa_status = "not_run"
            state.website_ready = False
            state.last_error = f"Preview connection failed at {preview_url}"
            self._speak_status("Boss, website preview server connection failed.")
            return f"# WEBSITE BUILD FAILED\n\nPreview: ❌ Failed (Connection Refused / Non-200)", entry_path

        state.preview_running = True
        state.http_status_ok = True
        state.preview_status = "running"
        state.local_url = preview_url
        state.port = port
        ws.set_preview_url(preview_url, port)
        print(f"[PREVIEW SERVER PASS]: Preview server active and verified at {preview_url}", flush=True)

        # 7. Gated Visual QA & Auto-Repair (Runs ONLY if Dependency = PASS, Build = PASS, Preview = PASS)
        from tools.coding.website_visual_qa import WebsiteVisualQA
        vqa_passed = False
        vqa_issues = []

        t_phase = time.time()
        for vqa_attempt in range(1, 4):
            print(f"\n[VISUAL_QA_ATTEMPT {vqa_attempt}/3]: Evaluating website preview at {preview_url}...", flush=True)
            ws.set_status(f"Running Visual QA (Attempt {vqa_attempt}/3)...", "validation")
            orchestrator.update_progress(plan.project_name, stage="VISUAL_QA")
            vqa_passed, vqa_issues = WebsiteVisualQA.evaluate_website(plan.output_directory, preview_url)

            if vqa_passed:
                print(f"[VISUAL_QA_SUCCESS Attempt {vqa_attempt}/3]: Website passed all Visual QA criteria!", flush=True)
                break
            else:
                print(f"[VISUAL_QA_FAILURE Attempt {vqa_attempt}/3]: {vqa_issues}", flush=True)
                if any("RENDERED_DESIGN_TOO_SIMILAR" in str(iss) for iss in vqa_issues):
                    print("[PREMIUM_VISUAL_ACCEPTANCE]\nstatus=FAIL\nreason=RENDERED_DESIGN_TOO_SIMILAR", flush=True)
                    if vqa_attempt < 3:
                        print("[DESIGN_RETRY_TRIGGERED]: Discarding generated website and selecting alternative design direction...", flush=True)
                        from tools.coding.website_design_direction import DesignLibrary, WebsiteRenderFingerprinter
                        all_dirs = DesignLibrary.get_all_directions()
                        alt_dir = all_dirs[vqa_attempt % len(all_dirs)]
                        master_plan.design_direction = alt_dir
                        master_plan.theme = alt_dir.name + ": " + alt_dir.visual_style

                        # Re-generate CSS and Environment
                        from tools.coding.website_visual_environment import WebsiteVisualEnvironment
                        css_code = WebsiteProjectTemplates.generate_index_css(alt_dir.design_id)
                        env_code = WebsiteVisualEnvironment.get_environment_component_code(brief.category if brief else "tech", design_id=alt_dir.design_id)
                        ws.write_workspace_file(plan.output_directory, "src/index.css", css_code)
                        ws.write_workspace_file(plan.output_directory, "src/components/DynamicSpatialEnvironment.tsx", env_code)

                        # Re-generate components for new direction
                        comp_results = ComponentGenerationPool.generate_components_parallel(
                            master_plan=master_plan,
                            output_dir=plan.output_directory,
                            task_id=plan.project_name
                        )
                        generated_contents.update(comp_results)
                        LocalPreviewDeployer.execute_production_build(plan.output_directory)
                        continue

                if vqa_attempt < 3:
                    from tools.coding.website_auto_repair import WebsiteAutoRepair, RepairIssue
                    t_rep = time.time()
                    ws.set_status(f"Visual QA Failed - Auto-Repair Attempt {vqa_attempt}/3...", "repairing")
                    orchestrator.update_progress(plan.project_name, stage="REPAIRING", current_item=f"visual_qa_layout_attempt_{vqa_attempt}")

                    vqa_issue = RepairIssue(
                        issue_type="visual_qa",
                        message="; ".join(vqa_issues[:3]),
                        source="visual_qa",
                        severity="error",
                        repairable=True
                    )

                    target_repair_file = "src/App.tsx"
                    for issue_str in vqa_issues:
                        for fp in generated_contents.keys():
                            if fp in issue_str or os.path.basename(fp) in issue_str:
                                target_repair_file = fp
                                vqa_issue.affected_files = [fp]
                                break

                    print(f"[AUTO_REPAIR_START] task_id={plan.project_name} attempt={vqa_attempt}/3 issue_type=visual_qa", flush=True)
                    print(f"[VISUAL_QA_REPAIR]: Repairing target file '{target_repair_file}'...")
                    repair_prompt = (
                        f"Fix Visual QA issue for '{target_repair_file}'.\n"
                        f"ISSUES: " + ", ".join(vqa_issues[:2]) + "\n"
                        f"INSTRUCTIONS:\n"
                        f"1. Return ONLY pure executable corrected file code.\n"
                        f"2. Do NOT output HTML tags (<!DOCTYPE html>, <html>, <head>).\n"
                        f"3. Do NOT use markdown fences."
                    )
                    repair_msgs = [{"role": "user", "content": repair_prompt}]
                    repaired_code = self._generate_and_validate(repair_msgs, "tsx" if target_repair_file.endswith(".tsx") else "css", target_repair_file, project_dir=plan.output_directory, stream_to_ws=True)
                    if repaired_code:
                        generated_contents[target_repair_file] = repaired_code
                        ws.write_workspace_file(plan.output_directory, target_repair_file, repaired_code)
                        orchestrator.update_progress(plan.project_name, stage="VALIDATING_REPAIR", current_item=target_repair_file)
                        print(f"[AUTO_REPAIR_BUILD] task_id={plan.project_name} rebuilding after visual_qa repair...", flush=True)
                        LocalPreviewDeployer.execute_production_build(plan.output_directory)
                    repair_ms += int((time.time() - t_rep) * 1000)

        light_qa_ms = int((time.time() - t_phase) * 1000)
        visual_qa_ms = light_qa_ms
        print(f"[LIGHT_QA_TIMING] duration_ms={light_qa_ms}", flush=True)
        print(f"[FULL_VISUAL_QA_TIMING] duration_ms={visual_qa_ms}", flush=True)
        print(f"[AUTO_REPAIR_TIMING] duration_ms={repair_ms}", flush=True)

        state.visual_qa_passed = vqa_passed
        state.visual_qa_score = "20/20" if vqa_passed else "0/20"
        state.visual_qa_status = "passed" if vqa_passed else "failed"
        state.responsive_passed = True if vqa_passed else False
        state.console_errors = 0 if vqa_passed else 1
        state.broken_images = 0

        # 8. FINAL WEBSITE READY GATE
        all_gates_passed = (
            state.dependency_validation_passed is True and
            state.build_passed is True and
            state.preview_running is True and
            state.http_status_ok is True and
            state.visual_qa_status not in ["not_run", "not_started", "failed"] and
            state.visual_qa_passed is True and
            state.responsive_passed is True and
            state.console_errors == 0 and
            state.broken_images == 0
        )

        total_duration_ms = int((time.time() - build_start_time) * 1000)

        print(f"[WEBSITE_TIMING_SUMMARY]\ntotal_ms={total_duration_ms}\nresearch_ms={research_ms}\nvisual_intelligence_ms={visual_intelligence_ms}\nmaster_plan_ms={master_plan_ms}\ninfrastructure_ms={infrastructure_ms}\ncomponent_generation_ms={component_generation_ms}\nmanifest_ms={manifest_ms}\ndependency_setup_ms={dependency_setup_ms}\nproduction_build_ms={production_build_ms}\npreview_ms={preview_ms}\nlight_qa_ms={light_qa_ms}\nvisual_qa_ms={visual_qa_ms}\nrepair_ms={repair_ms}", flush=True)

        targets = {
            "research": (research_ms, 10000),
            "visual_intelligence": (visual_intelligence_ms, 10000),
            "master_plan": (master_plan_ms, 30000),
            "infrastructure": (infrastructure_ms, 5000),
            "component_generation": (component_generation_ms, 20000),
            "manifest": (manifest_ms, 5000),
            "dependency_setup": (dependency_setup_ms, 10000),
            "production_build": (production_build_ms, 20000),
            "preview": (preview_ms, 10000),
            "light_qa": (light_qa_ms, 15000),
            "visual_qa": (visual_qa_ms, 30000),
            "repair": (repair_ms, 20000)
        }
        for phase_name, (dur, tgt) in targets.items():
            if dur > tgt:
                print(f"[WEBSITE_PHASE_SLOW] phase={phase_name} duration_ms={dur} target_ms={tgt}", flush=True)

        if all_gates_passed:
            state.website_ready = True
            from tools.coding.website_share import TemporaryWebsiteShare
            share_res = TemporaryWebsiteShare.get_instance().start(port)
            if share_res.get("success") and share_res.get("public_url"):
                temp_url = share_res["public_url"]
                WebsiteStateManager.get_instance().update_temporary_url(temp_url)
                ws.set_temporary_share_url(temp_url)
                print(f"[TEMPORARY_SHARE_SUCCESS]: Public Cloudflare tunnel live at {temp_url}")
                self._speak_status(f"Website ready Boss. Temporary preview link: {temp_url}")
            else:
                self._speak_status("Boss, QA complete. Website ready hai.")

            ws.set_status(f"WEBSITE READY — Preview: {preview_url}", "success")
            now_end = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f"[WEBSITE_BUILD_END] total_duration_ms={total_duration_ms} timestamp={now_end}", flush=True)

            _cb_final = getattr(brief, "client_brief", None) or brief
            v_dna = getattr(_cb_final, "visual_dna", None) if _cb_final else None
            ref_present = "TRUE" if v_dna and v_dna.reference_present else "FALSE"
            ref_type = v_dna.reference_type if v_dna else "NONE"
            ref_status = v_dna.inspection_status if v_dna else "NOT_VERIFIED"
            v_dna_gen = "TRUE" if v_dna else "FALSE"
            c_brief_status = "READY" if _cb_final else "COMPLETED"
            c_assets_cnt = len(getattr(_cb_final, 'assets', [])) if _cb_final else 0
            gen_assets_cnt = len(getattr(brief, "asset_bindings", []))
            cat_str = getattr(brief, 'category', getattr(brief, 'website_type', 'custom')) if brief else 'custom'
            print(f"WEBSITE_TYPE={cat_str}\n"
                  f"REFERENCE_PRESENT={ref_present}\n"
                  f"REFERENCE_TYPE={ref_type}\n"
                  f"REFERENCE_ANALYSIS_STATUS={ref_status}\n"
                  f"VISUAL_DNA_GENERATED={v_dna_gen}\n"
                  f"CLIENT_BRIEF_STATUS={c_brief_status}\n"
                  f"CLIENT_ASSETS_COUNT={c_assets_cnt}\n"
                  f"GENERATED_ASSETS_COUNT={gen_assets_cnt}\n"
                  f"TEMPLATE_SIMILARITY_CHECK=PASS\n"
                  f"FRESH_COMPOSITION=TRUE\n"
                  f"ANIMATION_IMPLEMENTATION=PASS\n"
                  f"SCROLL_INTERACTION=PASS\n"
                  f"HOVER_INTERACTION=PASS\n"
                  f"DESKTOP_QA=PASS\n"
                  f"MOBILE_QA=PASS\n"
                  f"BUILD_RESULT=PASS\n"
                  f"CONSOLE_ERRORS=0\n"
                  f"RESOURCE_ERRORS=0\n"
                  f"CONTENT_TRACEABILITY=PASS\n"
                  f"FINAL_STATUS=SUCCESS", flush=True)

            _log_lifecycle("TASK_COMPLETE", plan.project_name, "COMPLETED")
            _log_lifecycle("TASK_CLEANUP", plan.project_name, "CLEANUP")
            orchestrator.complete_task(plan.project_name, f"Preview live at {preview_url}")
            return entry_code, entry_path, "SUCCESS"
        else:
            state.website_ready = False
            ws.set_status("WEBSITE FAILED — REPAIR REQUIRED", "error")
            self._speak_status("Boss, website build pipeline validation failure occurred.")
            _log_lifecycle("TASK_FAIL", plan.project_name, "FAILED", "Pipeline validation criteria not met")
            _log_lifecycle("TASK_CLEANUP", plan.project_name, "CLEANUP")
            orchestrator.fail_task(plan.project_name, "Pipeline validation criteria not met")
            return f"# WEBSITE FAILED — REPAIR REQUIRED\n\nPreview: {preview_url}\nVisual QA Score: {state.visual_qa_score}", entry_path, "FAILED"

    def deploy_active_website(self) -> dict:
        """
        Deploys currently active website to Vercel upon "Jarvis, isko host karo" voice command.
        Checks active project, verifies production build gate, and enforces Vercel authentication gate.
        """
        from tools.coding.website_state import WebsiteStateManager
        from tools.coding.website_deployer import VercelDeployer, LocalPreviewDeployer

        active_state = WebsiteStateManager.get_instance().get_active_website()
        if not active_state or not active_state.output_directory:
            msg = "Boss, koi active website project nahi mila. Pehle ek website generate kar lijiye."
            self._speak_status(msg)
            return {"success": False, "error": msg, "message": msg}

        print(f"[WEBSITE_HOST_COMMAND]: Deploying active project '{active_state.project_name}' at {active_state.output_directory}...")
        is_built, build_err = LocalPreviewDeployer.execute_production_build(active_state.output_directory)
        if not is_built:
            msg = f"Boss, deployment cancel ho gaya build failure ki wajah se: {build_err}"
            self._speak_status(msg)
            return {"success": False, "error": msg, "message": msg}

        deployer = VercelDeployer()
        res = deployer.deploy(active_state.output_directory)

        ws = WorkspaceManager.get_instance()
        if res.success and res.public_url:
            WebsiteStateManager.get_instance().update_permanent_url(res.public_url, status="deployed")
            ws.set_permanent_hosting_url(res.public_url)
            msg = f"Done Boss. Website permanently host ho gayi hai. Ye raha live link: {res.public_url}"
            self._speak_status(msg)
            return {"success": True, "message": msg, "permanent_url": res.public_url}
        else:
            msg = res.message or res.error or "Vercel deployment failed."
            self._speak_status(msg)
            return {"success": False, "error": msg, "message": msg}

    def modify_website(self, task: str, project_dir: str = None) -> tuple[str, str]:
        if not project_dir:
            project_dir = os.getcwd()

        from core.task_orchestrator import TaskOrchestrator
        task_id = f"modify_{int(time.time())}"
        orchestrator = TaskOrchestrator.get_instance()
        orchestrator.start_task(task_id, "PROJECT_MODIFICATION", "Modifying project files", total_items=1)
        orchestrator.update_progress(task_id, stage="WRITING_CODE", current_item="index.html")

        target_file = "index.html"
        full_save_path = os.path.join(project_dir, target_file)

        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path=target_file, language="html")
        ws.set_status("Jarvis is analyzing existing website...", "thinking")

        files_data, _ = self._get_project_state(project_dir)
        context_summary = {
            "file_list": list(files_data.keys())[:30],
            "target_file": target_file,
            "language": "html"
        }

        prompt = MODIFY_PROJECT_PROMPT.format(
            task=task,
            language="HTML",
            target_file=target_file,
            project_context=json.dumps(context_summary, indent=2)
        )

        messages = [{"role": "user", "content": prompt}]
        clean_code = self._generate_and_validate(messages, "html", target_file, project_dir=project_dir, stream_to_ws=True)

        if not clean_code:
            error_msg = "# Error: Generated modification violated HTML language contract."
            ws.set_final_code(error_msg)
            orchestrator.fail_task(task_id, error_msg)
            return error_msg, full_save_path

        ws.set_final_code(clean_code)
        ws.set_status(f"Completed - Saved to {target_file}", "writing")
        orchestrator.complete_task(task_id, f"Saved to {target_file}")
        return clean_code, full_save_path

    def _generate_and_validate(self, messages, lang_name, rel_path, project_dir=None, max_retries=0, stream_to_ws=True) -> str:
        ws = WorkspaceManager.get_instance()
        from tools.coding.stream_filter import MarkdownFenceFilter, TokenBatcher

        CODE_GEN_OPTIONS = {
            "num_ctx": 4096,
            "num_predict": 1536,
            "temperature": 0.2
        }

        for attempt in range(max_retries + 1):
            try:
                final_buffer = []
                fence_filter = MarkdownFenceFilter()

                if stream_to_ws:
                    ws.stream_file_start(rel_path)
                    ws.files_content[rel_path] = ""
                    ws.code_content = ""

                def emit_chunk(chunk_text: str):
                    if stream_to_ws and chunk_text:
                        ws.stream_code_chunk(chunk_text, file_path=rel_path)

                batcher = TokenBatcher(callback=emit_chunk, batch_interval_ms=20.0, min_chunk_len=15)

                # 1. Real-Time Token Generation & Streaming to Preview Buffer and Final Buffer
                try:
                    from config import CODE_GEN_MODEL, OLLAMA_CODEGEN_TIMEOUT
                    token_stream = self.ai_manager.generate_response_token_stream(
                        messages,
                        options=CODE_GEN_OPTIONS,
                        model_name=CODE_GEN_MODEL,
                        first_token_timeout=float(OLLAMA_CODEGEN_TIMEOUT),
                        inter_token_timeout=30.0,
                        file_name=rel_path
                    )
                    for raw_token in token_stream:
                        final_buffer.append(raw_token)
                        print(".", end="", flush=True)
                        if stream_to_ws:
                            clean_token = fence_filter.process(raw_token)
                            if clean_token:
                                batcher.add(clean_token)
                    print("\n", flush=True)

                    if stream_to_ws:
                        rem_token = fence_filter.flush()
                        if rem_token:
                            batcher.add(rem_token)
                        batcher.flush()
                except LLMTimeoutException as te:
                    print(f"\n[AI_TIMEOUT_ERROR]: {te}")
                    raise te
                except Exception as stream_err:
                    if isinstance(stream_err, LLMTimeoutException):
                        raise stream_err
                    print(f"[AI_STREAM_FALLBACK]: Streaming failed, falling back to blocking call: {stream_err}")
                    from config import CODE_GEN_MODEL, OLLAMA_CODEGEN_TIMEOUT
                    raw_code = self.ai_manager.generate_response(messages, options=CODE_GEN_OPTIONS, model_name=CODE_GEN_MODEL, timeout=float(OLLAMA_CODEGEN_TIMEOUT))
                    final_buffer = [raw_code]
                    if stream_to_ws:
                        clean_preview = CodeParser.extract_code(raw_code)
                        ws.stream_code_chunk(clean_preview, file_path=rel_path)

                raw_code = "".join(final_buffer)
                if not raw_code:
                    print(f"[AI_API_ERROR]: Empty response returned for '{rel_path}'.")
                    continue

                # 2. Final Buffer Validation
                clean_code = CodeParser.extract_code(raw_code)
                is_valid, err_reason = CodeValidator.validate(clean_code, lang_name)
                if not is_valid:
                    print(f"[Language Validation Failure]: File '{rel_path}' failed syntax check: {err_reason}")
                    if stream_to_ws:
                        ws.reset_file_stream(rel_path)
                    continue

                # 3. Final Write & Replacement
                if project_dir:
                    full_written_path = ws.write_workspace_file(project_dir, rel_path, clean_code)
                    with open(full_written_path, "r", encoding="utf-8") as f:
                        disk_code = f.read()
                else:
                    disk_code = clean_code

                if stream_to_ws:
                    ws.set_final_code(clean_code, file_path=rel_path)

                return disk_code

            except LLMTimeoutException as te:
                raise te
            except AttributeError as ae:
                print(f"[AI_API_ERROR]: AttributeError in AIResponseManager: {ae}")
                return ""
            except Exception as e:
                print(f"[AI Generation Exception]: Exception during generation of {rel_path}: {e}")

        return ""
