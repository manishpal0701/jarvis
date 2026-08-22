import os
import socket
import http.server
import socketserver
import threading
import time
import webbrowser

def find_free_port(start_port=5173):
    """Finds an available local TCP port starting from start_port."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

class DirectoryHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy HTTP server console logs
        pass

class LocalWebsiteServer:
    """
    Lightweight background HTTP daemon for serving local website build projects.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.server = None
        self.server_thread = None
        self.port = 0
        self.project_dir = ""
        self.is_running = False

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = LocalWebsiteServer()
            return cls._instance

    def start_preview(self, project_dir: str, port: int = None, open_browser: bool = True) -> tuple[str, int]:
        """
        Serves project_dir (or project_dir/dist if present) on a dynamic local port and opens browser preview.
        Returns tuple of (url, port).
        """
        with self._lock:
            if self.is_running:
                self.stop_preview()

            dist_path = os.path.join(project_dir, "dist")
            serve_dir = dist_path if os.path.exists(dist_path) else project_dir

            self.project_dir = serve_dir
            self.port = port or find_free_port(5173)

            handler = lambda *args, **kwargs: DirectoryHTTPRequestHandler(*args, directory=serve_dir, **kwargs)
            self.server = socketserver.TCPServer(('127.0.0.1', self.port), handler)

            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.is_running = True
            time.sleep(0.3)

            url = f"http://127.0.0.1:{self.port}"
            if open_browser:
                webbrowser.open(url)
            return url, self.port

    def stop_preview(self):
        with self._lock:
            if self.server:
                try:
                    self.server.shutdown()
                    self.server.server_close()
                except Exception:
                    pass
                self.server = None
                self.is_running = False
