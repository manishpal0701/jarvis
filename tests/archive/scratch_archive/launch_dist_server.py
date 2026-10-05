import http.server
import socketserver
import os
import sys

def main():
    target_dir = os.path.abspath("workspace_e2e_test/websites/jarvis_a_modern_premium_ai_portfolio_for_manish/dist")
    if not os.path.exists(target_dir):
        target_dir = os.path.abspath("workspace_e2e_test/websites/jarvis_a_modern_premium_ai_portfolio_for_manish")

    os.chdir(target_dir)
    port = 5173

    handler = http.server.SimpleHTTPRequestHandler
    print(f"SERVING_DIR={target_dir}")
    print(f"PREVIEW_URL=http://127.0.0.1:{port}")

    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()
