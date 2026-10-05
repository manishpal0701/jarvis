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
        self.servers = []
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
        dist_path = os.path.join(project_dir, "dist")
        serve_dir = dist_path if os.path.exists(dist_path) else project_dir

        target_port = port or find_free_port(5173)

        handler = lambda *args, **kwargs: DirectoryHTTPRequestHandler(*args, directory=serve_dir, **kwargs)

        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            allow_reuse_address = True
            daemon_threads = True

        try:
            server = ThreadedTCPServer(('127.0.0.1', target_port), handler)
        except Exception:
            target_port = find_free_port(target_port + 1)
            server = ThreadedTCPServer(('127.0.0.1', target_port), handler)

        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        with self._lock:
            self.servers.append(server)
            self.port = target_port
            self.project_dir = serve_dir
            self.is_running = True

        url = f"http://127.0.0.1:{target_port}"
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return url, target_port

    def stop_preview(self):
        with self._lock:
            for s in self.servers:
                try:
                    s.server_close()
                except Exception:
                    pass
            self.servers.clear()
            self.is_running = False
