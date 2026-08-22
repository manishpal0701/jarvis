import os
import json
import time
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

    def _speak_status(self, text: str):
        print(f"[Jarvis Status]: {text}")

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
                return self.build_website(task, project_dir=project_dir, brief=brief, open_browser=open_browser)
            elif mode == "PROJECT_MODIFICATION":
                return self.modify_website(task, project_dir=project_dir)
            else:
                return self._generate_standalone(task, project_dir=project_dir)
        except Exception as e:
            err_msg = f"# Error: Code generation failed during processing stage: {e}"
            print(f"[CodeAssistant Error]: {err_msg}")
            target_file = self.detect_target_file(task, project_dir)[0]
            save_path = os.path.join(project_dir or os.getcwd(), target_file)
            return err_msg, save_path

    def _generate_standalone(self, task: str, project_dir: str = None) -> tuple[str, str]:
        if not project_dir:
            project_dir = os.getcwd()

        from tools.coding.protected_file_validator import ProtectedFileValidator

        rel_path, lang, ext = self.detect_target_file(task, project_dir)
        rel_path, _ = ProtectedFileValidator.protect(rel_path)
        full_save_path = os.path.join(project_dir, rel_path)

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
            return error_msg, full_save_path

        ws.set_final_code(clean_code)
        ws.set_status(f"Completed - Saved to {rel_path}", "writing")
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

        plan = WebsiteProjectPlanner.plan_project(task, project_dir, brief=brief)
        os.makedirs(plan.output_directory, exist_ok=True)
        print(f"[WEBSITE_PROJECT]\nProject directory: {plan.output_directory}")

        ws_files = [{"path": f.path, "lang": f.language} for f in plan.files]
        ws = WorkspaceManager.get_instance()
        ws.open_workspace(file_path=plan.entry_file, language="tsx" if plan.framework == "react" else "html", project_files=ws_files)
        ws.set_status(f"Jarvis is planning website project '{plan.project_name}'...", "thinking")
        self._speak_status("Alright Boss, website structure plan karke files build karta hoon.")

        generated_contents = {}
        all_passed = True
        repaired_any = False

        from tools.coding.website_asset_planner import WebsiteAssetPlanner
        manifest = WebsiteAssetPlanner.plan_assets(brief, plan.output_directory)
        manifest_desc = json.dumps(manifest.to_dict(), indent=2)
        formatted_brief = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
        formatted_brief += f"\n\n**Visual Assets Manifest**:\n{manifest_desc}"

        INFRASTRUCTURE_FILES = {"package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx"}

        for file_plan in plan.files:
            ws.set_file_info(file_plan.path, file_plan.language)
            ws.set_status(f"Processing {file_plan.path}...", "writing")

            # 1. Zero-LLM Infrastructure Generation
            if file_plan.path in INFRASTRUCTURE_FILES:
                print(f"[ZERO-LLM INFRASTRUCTURE]: Generating {file_plan.path} deterministically...")
                ws.stream_file_start(file_plan.path)
                if file_plan.path == "package.json":
                    clean_code = WebsiteProjectTemplates.generate_package_json(
                        biz_name=brief.business_name if brief else "React App",
                        project_name=plan.project_name
                    )
                elif file_plan.path == "tsconfig.json":
                    clean_code = WebsiteProjectTemplates.generate_tsconfig()
                elif file_plan.path == "vite.config.ts":
                    clean_code = WebsiteProjectTemplates.generate_vite_config()
                elif file_plan.path == "index.html":
                    clean_code = WebsiteProjectTemplates.generate_index_html(
                        biz_name=brief.business_name if brief else "Website",
                        title=f"{brief.subject.name} Portfolio" if brief and brief.subject and brief.subject.name else "Website"
                    )
                elif file_plan.path == "src/main.tsx":
                    clean_code = WebsiteProjectTemplates.generate_main_tsx()

                ws.reset_code("")
                ws.stream_code_chunk(clean_code)
                full_written = ws.write_workspace_file(plan.output_directory, file_plan.path, clean_code)
                generated_contents[file_plan.path] = clean_code
                continue

            # 2. LLM UI File Generation (Capped attempts: MAX_GENERATION_ATTEMPTS = 2, MAX_REPAIR_ATTEMPTS = 2)
            html_context = generated_contents.get("index.html", "N/A") if file_plan.path == "style.css" else "N/A"
            framework = plan.framework if hasattr(plan, 'framework') else "vanilla"

            if framework == "nextjs":
                prompt_tmpl = NEXTJS_FILE_PROMPT
            elif framework == "spring_boot":
                prompt_tmpl = SPRING_BOOT_FILE_PROMPT
            elif framework == "react":
                prompt_tmpl = REACT_FILE_PROMPT
            elif framework == "vue":
                prompt_tmpl = VUE_FILE_PROMPT
            else:
                prompt_tmpl = VANILLA_FILE_PROMPT

            prompt = prompt_tmpl.format(
                task=task,
                target_file=file_plan.path,
                language=file_plan.language.upper(),
                role=file_plan.role,
                project_plan=json.dumps([{"path": f.path, "role": f.role} for f in plan.files], indent=2),
                website_brief=formatted_brief,
                html_context=html_context,
                business_name=brief.business_name if brief else "Brand",
                category=brief.category if brief else "custom"
            )

            messages = [{"role": "user", "content": prompt}]
            clean_code = None
            gen_error = ""

            # Generation Attempts (Max 2)
            for gen_attempt in range(1, 3):
                print(f"[GENERATION_ATTEMPT {gen_attempt}/2] Generating UI file: {file_plan.path}...")
                clean_code = self._generate_and_validate(messages, file_plan.language, file_plan.path, project_dir=plan.output_directory, max_retries=0, stream_to_ws=True)
                if clean_code:
                    break
                gen_error = f"Generation failed syntax validation on attempt {gen_attempt}."

            # Repair Attempts (Max 2 if generation failed)
            if not clean_code:
                for repair_attempt in range(1, 3):
                    print(f"[REPAIR_ATTEMPT {repair_attempt}/2] Repairing UI file: {file_plan.path}...")
                    ws.set_status(f"Repairing {file_plan.path}...", "repairing")
                    repair_prompt = (
                        f"You are repairing an existing project file.\n\n"
                        f"Return ONLY the complete corrected file.\n\n"
                        f"Do not explain anything.\n"
                        f"Do not use Markdown fences.\n"
                        f"Do not modify unrelated files.\n"
                        f"Preserve the intended UI and functionality.\n\n"
                        f"FILE:\n{file_plan.path}\n\n"
                        f"VALIDATION ERROR:\n{gen_error or 'Invalid syntax or formatting'}"
                    )
                    repair_messages = [{"role": "user", "content": repair_prompt}]
                    clean_code = self._generate_and_validate(repair_messages, file_plan.language, file_plan.path, project_dir=plan.output_directory, max_retries=0, stream_to_ws=True)
                    if clean_code:
                        print(f"[REPAIR_ATTEMPT {repair_attempt}/2] Repair succeeded for {file_plan.path}!")
                        repaired_any = True
                        break

            if not clean_code:
                print(f"[BUILD_FAILED]: File {file_plan.path} failed generation and repair attempts.")
                all_passed = False
                break

            generated_contents[file_plan.path] = clean_code
            time.sleep(0.01)

        entry_path = os.path.join(plan.output_directory, plan.entry_file)
        entry_code = generated_contents.get(plan.entry_file, "")

        if not all_passed:
            ws.set_status("Website Build Failed - UI Generation Failure", "error")
            self._speak_status("Boss, website UI generation process failed.")
            return "# Error: Website file generation failed", entry_path

        if repaired_any:
            print("[WHOLE-PROJECT REVALIDATION]: File repairs occurred. Revalidating entire project structure...")

        # 2. Level 1 — Cross-File Asset & Dependency Validation
        ws.set_status("Running Level 1 Asset & Infrastructure Validation...", "validation")
        is_asset_valid, asset_err = CodeValidator.validate_website_assets(plan.output_directory, plan)
        if not is_asset_valid:
            print(f"[Level 1 Validation Failure]: {asset_err}")
            ws.set_status(f"Validation Failed: {asset_err}", "error")
            self._speak_status(f"Boss, website asset validation failed: {asset_err}")
            return f"# Error: {asset_err}", entry_path

        # 3. Level 2 — Website UI Completeness Validation
        ws.set_status("Running Level 2 UI Completeness Validation...", "validation")
        is_l2_valid, l2_err = CodeValidator.validate_level2_completeness(plan.output_directory, brief)
        if not is_l2_valid:
            print(f"[Level 2 Completeness Failure]: {l2_err}")
            ws.set_status(f"Level 2 Completeness Failed: {l2_err}", "error")
            self._speak_status(f"Boss, website Level 2 UI completeness failed: {l2_err}")
            return f"# Error: Level 2 Completeness Failed. {l2_err}", entry_path

        # 4. Anti-Fabrication Final Gate
        ws.set_status("Running Anti-Fabrication Security Validation...", "validation")
        is_af_valid, af_err = CodeValidator.validate_anti_fabrication(plan.output_directory, brief)
        if not is_af_valid:
            print(f"[Anti-Fabrication Gate Failure]: {af_err}")
            ws.set_status(f"Anti-Fabrication Gate Failed: {af_err}", "error")
            self._speak_status(f"Boss, anti-fabrication validation failed: {af_err}")
            return f"# Error: Anti-Fabrication Failure. {af_err}", entry_path

        # 4.5. Dependency Closure Gate
        ws.set_status("Running Dependency Closure Validation...", "validation")
        is_dep_valid, dep_err = CodeValidator.validate_dependency_closure(plan.output_directory)
        if not is_dep_valid:
            print(f"[Dependency Closure Failure]: {dep_err}")
            ws.set_status(f"Dependency Validation Failed: {dep_err}", "error")
            self._speak_status(f"Boss, dependency closure validation failed: {dep_err}")
            return f"# Error: {dep_err}", entry_path

        # 5. Mandatory Production Build Gate (npm install + npm run build -> dist/) with Build Auto-Repair
        ws.set_status("Building production assets (npm install && npm run build)...", "building")
        print(f"[BUILD_PROJECT_DIR]\n{plan.output_directory}")
        from tools.coding.website_deployer import LocalPreviewDeployer
        is_build_ok, build_err = LocalPreviewDeployer.execute_production_build(plan.output_directory)

        if not is_build_ok:
            for build_repair_attempt in range(1, 3):
                print(f"[BUILD_REPAIR_ATTEMPT {build_repair_attempt}/2]: Production build failed: {build_err}. Attempting auto-repair...")
                ws.set_status(f"Build Repair Attempt {build_repair_attempt}/2...", "repairing")

                # Identify offending file from build_err log
                offending_file = None
                for fp in generated_contents.keys():
                    if fp in build_err or os.path.basename(fp) in build_err:
                        offending_file = fp
                        break
                if not offending_file:
                    if "src/index.css" in generated_contents or "index.css" in build_err:
                        offending_file = "src/index.css"
                    else:
                        offending_file = "src/App.tsx"

                print(f"[BUILD_REPAIR_ATTEMPT {build_repair_attempt}/2]: Identified offending file: {offending_file}")
                file_lang = "css" if offending_file.endswith(".css") else "tsx"

                repair_prompt = (
                    f"You are repairing a project file that caused a production build failure during 'npm run build'.\n\n"
                    f"Return ONLY the complete corrected file.\n"
                    f"Do not explain anything.\n"
                    f"Do not use Markdown fences.\n"
                    f"Preserve the intended UI and functionality.\n\n"
                    f"FILE:\n{offending_file}\n\n"
                    f"BUILD ERROR LOG:\n{build_err}"
                )
                repair_messages = [{"role": "user", "content": repair_prompt}]
                repaired_code = self._generate_and_validate(repair_messages, file_lang, offending_file, project_dir=plan.output_directory, max_retries=0, stream_to_ws=True)

                if repaired_code:
                    print(f"[BUILD_REPAIR_ATTEMPT {build_repair_attempt}/2]: Repaired file {offending_file}. Writing and revalidating whole project...")
                    generated_contents[offending_file] = repaired_code

                    # Whole project revalidation
                    is_asset_valid, asset_err = CodeValidator.validate_website_assets(plan.output_directory, plan)
                    if not is_asset_valid:
                        build_err = asset_err
                        continue
                    is_l2_valid, l2_err = CodeValidator.validate_level2_completeness(plan.output_directory, brief)
                    if not is_l2_valid:
                        build_err = l2_err
                        continue
                    is_af_valid, af_err = CodeValidator.validate_anti_fabrication(plan.output_directory, brief)
                    if not is_af_valid:
                        build_err = af_err
                        continue
                    is_dep_valid, dep_err = CodeValidator.validate_dependency_closure(plan.output_directory)
                    if not is_dep_valid:
                        build_err = dep_err
                        continue

                    # Rerun npm build
                    is_build_ok, build_err = LocalPreviewDeployer.execute_production_build(plan.output_directory)
                    if is_build_ok:
                        print(f"[BUILD_REPAIR_ATTEMPT {build_repair_attempt}/2]: Production build succeeded after auto-repair!")
                        break

        if not is_build_ok:
            print(f"[Production Build Gate Failure]: {build_err}")
            ws.set_status(f"Production Build Failed: {build_err}", "error")
            self._speak_status(f"Boss, production build failed: {build_err}")
            return f"# Error: Production Build Failed. {build_err}", entry_path

        # 6. Production Build Gate Passed -> Start Local Preview Server & Open Browser!
        from tools.coding.local_website_server import LocalWebsiteServer
        server = LocalWebsiteServer.get_instance()
        preview_url, port = server.start_preview(plan.output_directory, open_browser=open_browser)

        # 7. Visual QA & Targeted Auto-Repair Gate (Max 3 iterations)
        from tools.coding.website_visual_qa import WebsiteVisualQA
        vqa_passed = False
        vqa_issues = []

        for vqa_attempt in range(1, 4):
            print(f"\n[VISUAL_QA_ATTEMPT {vqa_attempt}/3]: Evaluating website preview at {preview_url}...")
            ws.set_status(f"Running Visual QA (Attempt {vqa_attempt}/3)...", "validation")
            vqa_passed, vqa_issues = WebsiteVisualQA.evaluate_website(plan.output_directory, preview_url)

            if vqa_passed:
                print(f"[VISUAL_QA_SUCCESS Attempt {vqa_attempt}/3]: Website passed all Visual QA criteria!")
                break
            else:
                print(f"[VISUAL_QA_FAILURE Attempt {vqa_attempt}/3]: {vqa_issues}")
                if vqa_attempt < 3:
                    ws.set_status(f"Visual QA Failed - Repairing Attempt {vqa_attempt}/3...", "repairing")
                    # Identify failing file from vqa_issues
                    target_repair_file = "src/App.tsx"
                    for issue_str in vqa_issues:
                        for fp in generated_contents.keys():
                            if fp in issue_str or os.path.basename(fp) in issue_str:
                                target_repair_file = fp
                                break

                    print(f"[VISUAL_QA_REPAIR]: Repairing target file '{target_repair_file}'...")
                    repair_prompt = (
                        f"You are repairing a website component file that failed Visual QA.\n\n"
                        f"Return ONLY the complete corrected file.\n"
                        f"Do not explain anything.\n"
                        f"Do not use Markdown fences.\n"
                        f"STRICT ZERO PLACEHOLDER RULE: Absolutely NO 'Navbar Section', 'Hero Section', 'Explore Hero', 'Lorem ipsum', or 'TODO'.\n\n"
                        f"FILE:\n{target_repair_file}\n\n"
                        f"VISUAL QA ISSUES:\n" + "\n".join(vqa_issues)
                    )
                    repair_msgs = [{"role": "user", "content": repair_prompt}]
                    repaired_code = self._generate_and_validate(repair_msgs, "tsx" if target_repair_file.endswith(".tsx") else "css", target_repair_file, project_dir=plan.output_directory, stream_to_ws=True)
                    if repaired_code:
                        generated_contents[target_repair_file] = repaired_code
                        LocalPreviewDeployer.execute_production_build(plan.output_directory)

        if not vqa_passed:
            print(f"[VISUAL_QA_WARN]: Visual QA completed with warnings: {vqa_issues}")

        ws.set_status(f"BUILD_SUCCESS - Preview: {preview_url}", "success")
        self._speak_status("Done Boss, website ready hai. Browser mein preview open kar diya.")

        return entry_code, entry_path

    def modify_website(self, task: str, project_dir: str = None) -> tuple[str, str]:
        if not project_dir:
            project_dir = os.getcwd()

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
            return error_msg, full_save_path

        ws.set_final_code(clean_code)
        ws.set_status(f"Completed - Saved to {target_file}", "writing")
        return clean_code, full_save_path

    def _generate_and_validate(self, messages, lang_name, rel_path, project_dir=None, max_retries=0, stream_to_ws=True) -> str:
        ws = WorkspaceManager.get_instance()
        from tools.coding.stream_filter import MarkdownFenceFilter, TokenBatcher

        CODE_GEN_OPTIONS = {
            "num_ctx": 4096,
            "num_predict": 2048,
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
                    token_stream = self.ai_manager.generate_response_token_stream(messages, options=CODE_GEN_OPTIONS)
                    for raw_token in token_stream:
                        final_buffer.append(raw_token)
                        if stream_to_ws:
                            clean_token = fence_filter.process(raw_token)
                            if clean_token:
                                batcher.add(clean_token)

                    if stream_to_ws:
                        rem_token = fence_filter.flush()
                        if rem_token:
                            batcher.add(rem_token)
                        batcher.flush()
                except Exception as stream_err:
                    print(f"[AI_STREAM_FALLBACK]: Streaming failed, falling back to blocking call: {stream_err}")
                    raw_code = self.ai_manager.generate_response(messages, options=CODE_GEN_OPTIONS)
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
                    continue

                # 3. Final Write & Replacement
                if project_dir:
                    full_written_path = ws.write_workspace_file(project_dir, rel_path, clean_code)
                    with open(full_written_path, "r", encoding="utf-8") as f:
                        disk_code = f.read()
                else:
                    disk_code = clean_code
                    if stream_to_ws:
                        ws.stream_file_end(rel_path)

                if stream_to_ws:
                    ws.set_final_code(clean_code, file_path=rel_path)

                return disk_code

            except AttributeError as ae:
                print(f"[AI_API_ERROR]: AttributeError in AIResponseManager: {ae}")
                return ""
            except Exception as e:
                print(f"[AI Generation Exception]: Exception during generation of {rel_path}: {e}")

        return ""
