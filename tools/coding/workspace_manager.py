import os
import socket
import threading
import time
import queue
import json
import webbrowser
from flask import Flask, Response, send_from_directory
from flask_cors import CORS

UI_DIR = os.path.join(os.path.dirname(__file__), "workspace_ui")

def find_free_port(start_port=5000):
    """Finds an available local TCP port starting from start_port."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

class WorkspaceManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.port = find_free_port()
        self.server_thread = None
        self.server_started = False
        self.browser_opened = False

        # State
        self.file_path = "main.py"
        self.language = "python"
        self.status = "Jarvis is ready"
        self.state_class = "thinking"
        self.code_content = ""
        self.project_files = [] # list of {"path": str, "lang": str}
        self.files_content = {}
        self.active_file_streaming = None

        # SSE Subscribers
        self.subscribers = []
        self.sub_lock = threading.Lock()

        # Flask App setup
        self.app = Flask(__name__, static_folder=UI_DIR)
        CORS(self.app)
        self._setup_routes()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = WorkspaceManager()
            return cls._instance

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return send_from_directory(UI_DIR, 'index.html')

        @self.app.route('/static/js/<path:path>')
        def static_js_fallback(path):
            return send_from_directory(UI_DIR, path)

        @self.app.route('/static/<path:path>')
        def static_fallback(path):
            return send_from_directory(UI_DIR, path)

        @self.app.route('/<path:path>')
        def static_files(path):
            return send_from_directory(UI_DIR, path)

        @self.app.route('/api/stream')
        def stream():
            def event_generator():
                q = queue.Queue()
                with self.sub_lock:
                    self.subscribers.append(q)

                current_code = self.files_content.get(self.file_path, self.code_content)
                init_data = {
                    "type": "init",
                    "file_path": self.file_path,
                    "language": self.language,
                    "status": self.status,
                    "state": self.state_class,
                    "code": current_code,
                    "project_files": self.project_files,
                    "all_files": self.files_content
                }
                yield f"data: {json.dumps(init_data)}\n\n"

                try:
                    while True:
                        data = q.get()
                        yield f"data: {json.dumps(data)}\n\n"
                except GeneratorExit:
                    with self.sub_lock:
                        if q in self.subscribers:
                            self.subscribers.remove(q)

            return Response(event_generator(), mimetype='text/event-stream')

        @self.app.route('/api/brief/status', methods=['GET'])
        def brief_status():
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.client_brief_ingestion import ClientBriefParser
            from tools.coding.website_session_manager import WebsiteSessionManager

            session = LocalClientBriefSession.get_instance()
            web_session = WebsiteSessionManager.get_instance()
            extracted = ClientBriefParser.parse_local_client_session(session)
            summary = session.get_pre_build_summary(extracted)

            assets_data = [
                {
                    "asset_id": a.asset_id,
                    "filename": a.original_filename,
                    "role": a.role,
                    "provenance": a.provenance,
                    "local_path": a.local_path
                }
                for a in session.assets
            ]

            references_data = [
                {
                    "ref_type": r.ref_type,
                    "source": r.source,
                    "title": r.title
                }
                for r in session.reference_items
            ]

            messages_data = [
                {
                    "message_id": m.message_id,
                    "sender": m.sender,
                    "text": m.text,
                    "timestamp": m.timestamp
                }
                for m in session.messages
            ]

            payload = {
                "session_state": web_session.state.value if hasattr(web_session.state, 'value') else str(web_session.state),
                "company_name": session.client_name or getattr(extracted, "company_name", "") or getattr(extracted, "client_name", ""),
                "website_type": session.website_type or getattr(extracted, "website_type", "UNKNOWN"),
                "business_description": session.business_description or getattr(extracted, "business_description", ""),
                "website_goal": getattr(session, "website_goal", ""),
                "target_audience": getattr(session, "target_audience", ""),
                "location": getattr(session, "location", ""),
                "contact_number": getattr(session, "contact_number", ""),
                "email": getattr(session, "email", ""),
                "address": getattr(session, "address", ""),
                "brand_description": getattr(session, "brand_description", ""),
                "brand_tone": getattr(session, "brand_tone", ""),
                "primary_color": getattr(session, "primary_color", ""),
                "secondary_color": getattr(session, "secondary_color", ""),
                "preferred_font": getattr(session, "preferred_font", ""),
                "logo_availability": getattr(session, "logo_availability", ""),
                "required_pages": getattr(session, "required_pages", ""),
                "required_sections": getattr(session, "required_sections", ""),
                "features_functionality": getattr(session, "features_functionality", ""),
                "cta_action": getattr(session, "cta_action", ""),
                "special_requirements": getattr(session, "special_requirements", ""),
                "seo_requirements": getattr(session, "seo_requirements", ""),
                "hero_heading": getattr(session, "hero_heading", ""),
                "hero_description": getattr(session, "hero_description", ""),
                "about_content": getattr(session, "about_content", ""),
                "services_products": getattr(session, "services_products", ""),
                "pricing": getattr(session, "pricing", ""),
                "contact_info": getattr(session, "contact_info", ""),
                "social_links": getattr(session, "social_links", ""),
                "inspiration_style": getattr(session, "inspiration_style", ""),
                "missing_fields": getattr(extracted, "missing_fields", []),
                "summary": summary,
                "messages": messages_data,
                "assets": assets_data,
                "references": references_data
            }
            return Response(json.dumps(payload), mimetype='application/json')

        @self.app.route('/api/brief/message', methods=['POST'])
        def brief_message():
            from flask import request
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.website_session_manager import WebsiteSessionManager

            data = request.get_json(silent=True) or {}
            text = data.get("text", "").strip()

            web_session = WebsiteSessionManager.get_instance()
            if text:
                res_msg = web_session.handle_input(text)
            else:
                res_msg = "Please provide details in text."

            self._broadcast({"type": "brief_update", "action": "message_added", "text": text})
            return Response(json.dumps({"success": True, "message": res_msg}), mimetype='application/json')

        @self.app.route('/api/brief/upload', methods=['POST'])
        def brief_upload():
            from flask import request
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.website_session_manager import WebsiteSessionManager
            from tools.coding.client_brief_ingestion import ClientBriefParser

            session = LocalClientBriefSession.get_instance()
            web_session = WebsiteSessionManager.get_instance()
            upload_dir = os.path.abspath(os.path.join("data", "uploads"))
            os.makedirs(upload_dir, exist_ok=True)

            role = request.form.get("role", "unknown")
            caption = request.form.get("caption", "")

            uploaded_assets = []

            # Handle file uploads
            for file_key in request.files:
                file_obj = request.files[file_key]
                if file_obj and file_obj.filename:
                    filename = file_obj.filename
                    target_path = os.path.join(upload_dir, filename)
                    file_obj.save(target_path)

                    asset = session.add_attachment(target_path, caption=caption, role=role)
                    uploaded_assets.append({
                        "asset_id": asset.asset_id,
                        "filename": asset.original_filename,
                        "role": asset.role,
                        "local_path": asset.local_path
                    })

            web_session.brief = ClientBriefParser.parse_local_client_session(session)
            self._broadcast({"type": "brief_update", "action": "upload_completed", "assets": uploaded_assets})
            return Response(json.dumps({"success": True, "assets": uploaded_assets}), mimetype='application/json')

        @self.app.route('/api/brief/reset', methods=['POST', 'GET'])
        def brief_reset():
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.website_session_manager import WebsiteSessionManager
            session = LocalClientBriefSession.get_instance()
            web_session = WebsiteSessionManager.get_instance()
            session.reset_session()
            web_session.reset_session()
            self._broadcast({"type": "brief_update", "action": "session_reset"})
            return Response(json.dumps({"success": True, "message": "Client brief session reset to clean state"}), mimetype='application/json')

        @self.app.route('/api/brief/update', methods=['POST'])
        def brief_update_form():
            from flask import request
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.website_session_manager import WebsiteSessionManager
            from tools.coding.client_brief_ingestion import ClientBriefParser

            session = LocalClientBriefSession.get_instance()
            web_session = WebsiteSessionManager.get_instance()
            data = request.get_json(silent=True) or {}

            session.update_form_fields(data)

            company_name = data.get("company_name", "").strip()
            website_type = data.get("website_type", "").strip()
            business_description = data.get("business_description", "").strip()
            target_audience = data.get("target_audience", "").strip()
            services = data.get("services", "") or data.get("services_products", "")
            brand_preferences = data.get("brand_preferences", "") or data.get("brand_tone", "")
            required_sections = data.get("required_sections", "") or data.get("required_pages", "")
            special_requirements = data.get("special_requirements", "")

            update_parts = []
            if company_name:
                session.client_name = company_name
                update_parts.append(f"Company name: {company_name}")
            if website_type:
                update_parts.append(f"Website type: {website_type}")
            if business_description:
                update_parts.append(f"Description: {business_description}")
            if target_audience:
                update_parts.append(f"Target audience: {target_audience}")
            if services:
                update_parts.append(f"Services: {services}")
            if brand_preferences:
                update_parts.append(f"Brand style: {brand_preferences}")
            if required_sections:
                update_parts.append(f"Required pages: {required_sections}")
            if special_requirements:
                update_parts.append(f"Notes: {special_requirements}")

            if update_parts:
                full_text = "\n".join(update_parts)
                session.add_user_message(full_text)

            web_session.brief = ClientBriefParser.parse_local_client_session(session)

            self._broadcast({"type": "brief_update", "action": "form_updated"})
            return Response(json.dumps({"success": True}), mimetype='application/json')

        @self.app.route('/api/brief/remove_asset', methods=['POST'])
        def brief_remove_asset():
            from flask import request
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.website_session_manager import WebsiteSessionManager
            from tools.coding.client_brief_ingestion import ClientBriefParser

            session = LocalClientBriefSession.get_instance()
            web_session = WebsiteSessionManager.get_instance()
            data = request.get_json(silent=True) or {}
            asset_id = data.get("asset_id", "").strip()

            if asset_id:
                session.remove_asset(asset_id)
                web_session.brief = ClientBriefParser.parse_local_client_session(session)

            self._broadcast({"type": "brief_update", "action": "asset_removed", "asset_id": asset_id})
            return Response(json.dumps({"success": True}), mimetype='application/json')

        @self.app.route('/api/brief/reference', methods=['POST'])

        def brief_reference():
            from flask import request
            from tools.coding.local_client_brief import LocalClientBriefSession

            data = request.get_json(silent=True) or {}
            ref_type = data.get("ref_type", "URL").upper()
            source = data.get("source", "").strip()
            title = data.get("title", "").strip()

            session = LocalClientBriefSession.get_instance()

            if ref_type == "URL" and source:
                ref = session.add_reference_url(source, title=title)
            elif source:
                ref = session.add_reference_file(source, ref_type=ref_type)
            else:
                return Response(json.dumps({"success": False, "error": "No source provided"}), mimetype='application/json', status=400)

            self._broadcast({"type": "brief_update", "action": "reference_added", "ref_type": ref_type, "source": source})
            return Response(json.dumps({
                "success": True,
                "reference": {
                    "ref_type": ref.ref_type,
                    "source": ref.source,
                    "title": ref.title
                }
            }), mimetype='application/json')

        @self.app.route('/api/brief/approve', methods=['POST'])
        def brief_approve():
            from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
            from tools.coding.local_client_brief import LocalClientBriefSession
            from tools.coding.client_brief_ingestion import ClientBriefParser

            web_session = WebsiteSessionManager.get_instance()
            local_session = LocalClientBriefSession.get_instance()
            brief = ClientBriefParser.parse_local_client_session(local_session)
            web_session.brief = brief

            # Build a proper project directory slug from the client name
            import re
            client_name = (brief.company_name if brief and brief.company_name else "client_project").strip()
            slug = re.sub(r'[^a-z0-9]+', '_', client_name.lower()).strip('_')
            websites_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'websites')
            project_dir = os.path.abspath(os.path.join(websites_dir, slug))

            web_session.session_dir = project_dir
            if not web_session.original_command:
                web_session.original_command = f"Make a professional website for {client_name}"

            # CRITICAL: Set these flags BEFORE spawning background thread
            # so generate_code's CONVERSATIONAL_TRIGGER guard does not reset the brief
            web_session.WEBSITE_GENERATION_STARTED = True
            from tools.coding.website_session_manager import WebsiteSessionState as _WSS
            web_session.state = _WSS.APPROVED

            # Return 200 immediately — generation runs in background thread
            self._broadcast({"type": "status_update", "status": "⏳ Starting AI website generation...", "state": "building"})

            def run_generation():
                try:
                    web_session.state = WebsiteSessionState.WEBSITE_GENERATION
                    from tools.coding.code_assistant import CodeAssistant
                    assistant = CodeAssistant()
                    task_prompt = web_session.original_command
                    self._broadcast({"type": "status_update", "status": f"🚀 Generating website for {client_name}...", "state": "building"})
                    code, path, gen_status = assistant.generate_code(task_prompt, project_dir=project_dir, brief=brief)
                    if gen_status == "FAILED" or "Error" in str(code):
                        web_session.state = WebsiteSessionState.BUILD_FAILED
                        self._broadcast({"type": "status_update", "status": f"❌ Build failed: {str(code)[:200]}", "state": "error"})
                    else:
                        web_session.state = WebsiteSessionState.COMPLETED
                        self._broadcast({"type": "status_update", "status": "✓ Website Ready — Preview launched!", "state": "ready"})
                except Exception as ex:
                    self._broadcast({"type": "status_update", "status": f"❌ Generation error: {str(ex)[:200]}", "state": "error"})

            gen_thread = threading.Thread(target=run_generation, daemon=True)
            gen_thread.start()

            return Response(json.dumps({"success": True, "message": "Website generation started", "project_dir": project_dir, "client": client_name}), mimetype='application/json')


    def _broadcast(self, data):
        with self.sub_lock:
            for q in list(self.subscribers):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    @classmethod
    def check_health(cls, port=5000, timeout=1.0) -> bool:
        """Verifies if Workspace web server at http://127.0.0.1:{port} is responding with HTTP 200."""
        import urllib.request
        for test_path in ["/api/brief/status", "/"]:
            try:
                url = f"http://127.0.0.1:{port}{test_path}"
                req = urllib.request.Request(url, method='GET')
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                pass
        return False

    def ensure_started(self, timeout=15.0) -> bool:
        """
        Lazy starts the workspace web server thread if not already running.
        1. Checks if server is already responding on port 5000 or self.port.
        2. If not running, launches Flask server thread.
        3. Polls health endpoint with bounded timeout (max 15s).
        4. Logs telemetry: [WORKSPACE_SERVER] status=STARTING / READY / START_FAILED
        """
        print("[WORKSPACE_SERVER] status=CHECKING_HEALTH", flush=True)

        # First check if port 5000 is already serving the workspace
        if WorkspaceManager.check_health(5000):
            self.port = 5000
            self.server_started = True
            print(f"[WORKSPACE_SERVER] status=READY url=http://127.0.0.1:{self.port}", flush=True)
            return True

        if self.server_started and WorkspaceManager.check_health(self.port):
            print(f"[WORKSPACE_SERVER] status=READY url=http://127.0.0.1:{self.port}", flush=True)
            return True

        with self._lock:
            if not self.server_started or not WorkspaceManager.check_health(self.port):
                print(f"[WORKSPACE_SERVER] status=STARTING port={self.port}", flush=True)
                try:
                    self.server_thread = threading.Thread(
                        target=lambda: self.app.run(host='127.0.0.1', port=self.port, threaded=True, use_reloader=False),
                        daemon=True
                    )
                    self.server_thread.start()
                    self.server_started = True
                except Exception as ex:
                    print(f"[WORKSPACE_SERVER] status=START_FAILED error={ex}", flush=True)
                    return False

            # Bounded Health Check Loop
            start_t = time.time()
            while time.time() - start_t < timeout:
                if WorkspaceManager.check_health(self.port, timeout=0.5):
                    print(f"[WORKSPACE_SERVER] status=READY url=http://127.0.0.1:{self.port}", flush=True)
                    return True
                time.sleep(0.3)

            print(f"[WORKSPACE_SERVER] status=START_FAILED error=Timeout after {timeout}s", flush=True)
            return False

    def open_workspace(self, file_path="main.py", language="python", project_files=None, open_browser=True):
        """
        Ensures the workspace server is active and opens the browser tab.
        Reuses existing tab if already opened.
        """
        started = self.ensure_started()
        if not started:
            raise RuntimeError("SERVER_START_FAILED: Workspace server at http://127.0.0.1:5000 failed to respond to health check.")

        if project_files:
            self.set_project_files(project_files)
        self.set_file_info(file_path, language)

        if open_browser and not self.browser_opened:
            url = f"http://127.0.0.1:{self.port}"
            webbrowser.open(url)
            self.browser_opened = True

    def set_project_files(self, project_files):
        self.project_files = project_files
        for f in project_files:
            if f["path"] not in self.files_content:
                self.files_content[f["path"]] = ""
        self._broadcast({
            "type": "project_files_update",
            "files": project_files,
            "all_files": self.files_content
        })

    def set_file_info(self, file_path, language):
        self.file_path = file_path
        self.language = language
        if file_path not in self.files_content:
            self.files_content[file_path] = ""
        self.code_content = self.files_content[file_path]
        self._broadcast({
            "type": "file_update",
            "file_path": file_path,
            "language": language,
            "code": self.code_content
        })

    def set_status(self, status_text, state_class="writing"):
        self.status = status_text
        self.state_class = state_class
        self._broadcast({
            "type": "status_update",
            "status": status_text,
            "state": state_class
        })

    def set_preview_url(self, url: str, port: int):
        self._broadcast({
            "type": "status_update",
            "status": f"Local preview running at http://127.0.0.1:{port}",
            "preview_url": url
        })

    def set_temporary_share_url(self, public_url: str):
        self._broadcast({
            "type": "status_update",
            "status": "Temporary Cloudflare Share Link Active",
            "temporary_url": public_url
        })

    def set_permanent_hosting_url(self, public_url: str):
        self._broadcast({
            "type": "status_update",
            "status": "Permanently Deployed to Vercel",
            "permanent_url": public_url
        })

    def reset_code(self, initial_code=""):
        self.code_content = initial_code
        self.files_content[self.file_path] = initial_code
        self._broadcast({
            "type": "code_set",
            "file_path": self.file_path,
            "code": initial_code
        })

    def reset_file_stream(self, file_path: str):
        """Clears streamed buffer for a specific file when validation fails."""
        self.files_content[file_path] = ""
        if file_path == self.file_path:
            self.code_content = ""
        self._broadcast({
            "type": "code_set",
            "file_path": file_path,
            "code": "",
            "is_final": False,
            "error": "Generation failed — invalid model output"
        })

    def stream_code_chunk(self, chunk: str, file_path: str = None):
        target_path = file_path or self.file_path
        if target_path not in self.files_content:
            self.files_content[target_path] = ""

        self.files_content[target_path] += chunk
        if target_path == self.file_path:
            self.code_content = self.files_content[target_path]

        # Calculate current line & column metadata
        full_code = self.files_content[target_path]
        lines = full_code.split('\n')
        curr_line = len(lines)
        curr_col = len(lines[-1]) + 1

        self._broadcast({
            "type": "code_stream",
            "file_path": target_path,
            "chunk": chunk,
            "line": curr_line,
            "column": curr_col,
            "is_final": False
        })

    def stream_file_start(self, file_path: str):
        if self.active_file_streaming == file_path:
            return
        self.active_file_streaming = file_path
        self._broadcast({
            "type": "file_start",
            "file_path": file_path
        })

    def stream_file_end(self, file_path: str):
        self.active_file_streaming = None
        code_content = self.files_content.get(file_path, "")
        self._broadcast({
            "type": "file_end",
            "file_path": file_path,
            "code": code_content
        })

    def set_final_code(self, final_code: str, file_path: str = None):
        target_path = file_path or self.file_path
        self.files_content[target_path] = final_code
        if target_path == self.file_path:
            self.code_content = final_code

        self._broadcast({
            "type": "code_set",
            "file_path": target_path,
            "code": final_code,
            "is_final": True,
            "all_files": self.files_content
        })

    def write_workspace_file(self, project_dir: str, relative_path: str, content: str) -> str:
        """
        Single Public Save Pipeline Entry Point for all generated files.
        1. Protects system files (re-routes protected names like main.py -> generated_main.py).
        2. Validates path boundary and rejects path traversal attempts.
        3. Executes Atomic Write via internal write_file helper.
        4. Updates workspace state and broadcasts completion streaming event.
        """
        from tools.coding.path_validator import PathValidator
        from tools.coding.protected_file_validator import ProtectedFileValidator

        # 1. Protected File Guard
        safe_rel_path, protected_triggered = ProtectedFileValidator.protect(relative_path)
        if protected_triggered:
            print(f"[PROTECTED_FILE_GUARD]: Automatically renamed protected file '{relative_path}' -> '{safe_rel_path}'")

        # 2. Path Validation & Boundary Enforcement
        full_path = PathValidator.validate_and_resolve(project_dir, safe_rel_path)
        print(f"[WORKSPACE_WRITE]\nWriting: {full_path}")

        try:
            # 3. Atomic Write via internal helper
            _write_file_internal(full_path, content)

            print(f"[WORKSPACE_WRITE_SUCCESS]\n{full_path}")
            self.files_content[safe_rel_path] = content
            self.code_content = content

            # 4. Stream & UI Update
            self.set_final_code(content, file_path=safe_rel_path)
            self.stream_file_end(safe_rel_path)
            self.set_status(f"Completed - Saved to {safe_rel_path}", "writing")
            print(f"[STREAM_FILE_END] Completed file: {safe_rel_path}")
            return full_path
            return full_path

        except Exception as e:
            print(f"[WORKSPACE_WRITE_FAILURE]\n{full_path}\n{e}")
            raise

def _write_file_internal(filepath: str, content: str) -> None:
    """
    Internal/Private atomic file write helper used strictly by WorkspaceManager.
    Writes content to a temporary file, flushes, syncs, verifies content, and atomically replaces target file.
    """
    import tempfile
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    else:
        dir_name = "."

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=dir_name, delete=False, mode="w", encoding="utf-8", newline="\n") as tf:
            temp_path = tf.name
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())

        if not os.path.isfile(temp_path):
            raise RuntimeError(f"Atomic temporary file creation failed: {temp_path}")

        with open(temp_path, "r", encoding="utf-8") as rf:
            written_temp = rf.read()
        if written_temp != content:
            raise RuntimeError(f"Atomic temporary file content mismatch for {filepath}")

        # Atomic replacement with Windows PermissionError fallback
        try:
            os.replace(temp_path, filepath)
        except PermissionError:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            import shutil
            shutil.copyfile(temp_path, filepath)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        if not os.path.isfile(filepath):
            raise RuntimeError(f"Atomic file replace failed: {filepath}")

        with open(filepath, "r", encoding="utf-8") as vf:
            final_content = vf.read()
        if final_content != content:
            raise RuntimeError(f"Atomic file final content verification failed for {filepath}")

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise e

def write_file(filepath: str, content: str) -> None:
    """
    Internal write_file wrapper maintained for internal backward compatibility.
    Invokes _write_file_internal.
    """
    _write_file_internal(filepath, content)

