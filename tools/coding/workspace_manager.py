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

    def _broadcast(self, data):
        with self.sub_lock:
            for q in list(self.subscribers):
                try:
                    q.put_nowait(data)
                except Exception:
                    pass

    def ensure_started(self):
        """Lazy starts the workspace web server thread if not already running."""
        if not self.server_started:
            with self._lock:
                if not self.server_started:
                    self.server_thread = threading.Thread(
                        target=lambda: self.app.run(host='127.0.0.1', port=self.port, threaded=True, use_reloader=False),
                        daemon=True
                    )
                    self.server_thread.start()
                    self.server_started = True
                    time.sleep(0.5)

    def open_workspace(self, file_path="main.py", language="python", project_files=None):
        """
        Ensures the workspace server is active and opens the browser tab.
        Reuses existing tab if already opened.
        """
        self.ensure_started()
        if project_files:
            self.set_project_files(project_files)
        self.set_file_info(file_path, language)

        if not self.browser_opened:
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

    def reset_code(self, initial_code=""):
        self.code_content = initial_code
        self.files_content[self.file_path] = initial_code
        self._broadcast({
            "type": "code_set",
            "file_path": self.file_path,
            "code": initial_code
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
        self._broadcast({
            "type": "file_end",
            "file_path": file_path
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
            "is_final": True
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
            self.stream_file_end(safe_rel_path)
            self.set_status(f"Completed - Saved to {safe_rel_path}", "writing")
            print(f"[STREAM_FILE_END] Completed file: {safe_rel_path}")
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

        # Atomic replacement
        os.replace(temp_path, filepath)

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

