import os
import re
import shutil
import subprocess
import threading
import time
from typing import Dict, Any, Optional

class TemporaryWebsiteShare:
    """
    Temporary Public Website Sharing Agent using Cloudflare Quick Tunnels (cloudflared).
    Tunnels ONLY the specified local website preview port (http://127.0.0.1:<port>)
    and generates an external public URL (https://xxxx.trycloudflare.com).
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._public_url: str = ""
        self._port: int = 0
        self._is_active: bool = False

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = TemporaryWebsiteShare()
            return cls._instance

    @classmethod
    def is_cloudflared_available(cls) -> bool:
        """Returns True if cloudflared binary is installed and executable on system PATH."""
        return shutil.which("cloudflared") is not None

    def start(self, port: int, timeout_sec: int = 25) -> Dict[str, Any]:
        """
        Launches a Cloudflare Quick Tunnel for the given local port.
        Returns structured dictionary response.
        """
        with self._lock:
            if self._is_active and self._port == port and self._public_url:
                return {
                    "success": True,
                    "local_url": f"http://127.0.0.1:{port}",
                    "public_url": self._public_url,
                    "provider": "cloudflare",
                    "temporary": True
                }

            if self._process:
                self.stop()

            if not self.is_cloudflared_available():
                return {
                    "success": False,
                    "local_url": f"http://127.0.0.1:{port}",
                    "public_url": "",
                    "provider": "cloudflare",
                    "temporary": True,
                    "error": "cloudflared executable not found on system PATH. Install cloudflared binary to generate temporary public URLs."
                }

            cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"]
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            except Exception as e:
                return {
                    "success": False,
                    "local_url": f"http://127.0.0.1:{port}",
                    "public_url": "",
                    "provider": "cloudflare",
                    "temporary": True,
                    "error": f"Failed to launch cloudflared process: {e}"
                }

            self._port = port
            self._public_url = ""
            url_found_event = threading.Event()

            def _read_tunnel_output():
                url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
                for line in iter(self._process.stdout.readline, ''):
                    if not line:
                        break
                    match = url_pattern.search(line)
                    if match and not self._public_url:
                        self._public_url = match.group(0)
                        self._is_active = True
                        url_found_event.set()
                        break

            reader_thread = threading.Thread(target=_read_tunnel_output, daemon=True)
            reader_thread.start()

            got_url = url_found_event.wait(timeout=timeout_sec)
            if got_url and self._public_url:
                return {
                    "success": True,
                    "local_url": f"http://127.0.0.1:{port}",
                    "public_url": self._public_url,
                    "provider": "cloudflare",
                    "temporary": True
                }
            else:
                return {
                    "success": False,
                    "local_url": f"http://127.0.0.1:{port}",
                    "public_url": "",
                    "provider": "cloudflare",
                    "temporary": True,
                    "error": "Cloudflare Tunnel connection timed out before URL assignment."
                }

    def stop(self):
        """Safely terminates active cloudflared tunnel process."""
        with self._lock:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
            self._process = None
            self._public_url = ""
            self._port = 0
            self._is_active = False

    def get_public_url(self) -> str:
        with self._lock:
            return self._public_url
