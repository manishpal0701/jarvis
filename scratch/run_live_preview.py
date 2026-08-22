import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import time
import socket
import http.server
import socketserver

def find_free_port(start_port=5174):
    for p in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return start_port

def main():
    base_dir = os.path.abspath("workspace_e2e_test/websites/jarvis_a_modern_premium_ai_portfolio_for_manish")
    dist_dir = os.path.join(base_dir, "dist")
    serve_dir = dist_dir if os.path.exists(dist_dir) else base_dir

    port = find_free_port(5174)
    os.chdir(serve_dir)

    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)

    print(f"SERVED_DIRECTORY={serve_dir}")
    print(f"PORT={port}")
    print(f"URL=http://127.0.0.1:{port}")

    httpd.serve_forever()

if __name__ == "__main__":
    main()
