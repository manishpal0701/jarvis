import time
import os
import sys

BASE_DIR = os.path.abspath('.')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.local_website_server import LocalWebsiteServer
server = LocalWebsiteServer.get_instance()
url, port = server.start_preview('websites/bella_tavola_ristorante_italiano', port=5177, open_browser=False)
print(f"[BELLA TAVOLA PREVIEW SERVER ACTIVE] Listening on {url}")

while True:
    time.sleep(1)
