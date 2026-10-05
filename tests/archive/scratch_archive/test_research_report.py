import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.coding.website_researcher import WebsiteResearcher

def main():
    print("=" * 60)
    print("[WEB RESEARCH VERIFICATION]: Querying 'Tesla'...")
    print("=" * 60)
    ctx = WebsiteResearcher.research_company("Tesla")
    print(json.dumps(ctx.to_dict(), indent=2))
    print("=" * 60)

if __name__ == "__main__":
    main()
