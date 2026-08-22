import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import time
from tools.coding.local_website_server import LocalWebsiteServer

def main():
    target_dir = os.path.abspath("workspace_e2e_test/websites/jarvis_a_modern_premium_ai_portfolio_for_manish")
    server = LocalWebsiteServer.get_instance()
    url, port = server.start_preview(target_dir, port=5173, open_browser=False)
    print(f"PREVIEW_URL={url}")
    print(f"PORT={port}")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
