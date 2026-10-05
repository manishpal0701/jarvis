import os
import sys
import time
import json
import subprocess
import urllib.request

backend_dir = os.path.abspath("JARVIS App Projects/JARVIS_Weather_2c1acf9c/backend")
env = dict(os.environ)
env["PORT"] = "3007"

proc = subprocess.Popen(["node", "src/server.js"], cwd=backend_dir, env=env)
time.sleep(2.5)

try:
    print("\n==================================================")
    print("JARVIS WEATHER LIVE BACKEND API INTEGRATION TEST")
    print("==================================================")
    
    # 1. Health
    with urllib.request.urlopen("http://127.0.0.1:3007/api/health") as resp:
        print("[PASS] GET /api/health:", resp.read().decode())

    # 2. Current Weather (London)
    with urllib.request.urlopen("http://127.0.0.1:3007/api/weather/current?city=London") as resp:
        print("[PASS] GET /api/weather/current?city=London:", resp.read().decode()[:150])

    # 3. Current Weather (Tokyo)
    with urllib.request.urlopen("http://127.0.0.1:3007/api/weather/current?city=Tokyo") as resp:
        print("[PASS] GET /api/weather/current?city=Tokyo:", resp.read().decode()[:150])

    # 4. Forecast (Indore)
    with urllib.request.urlopen("http://127.0.0.1:3007/api/weather/forecast?city=Indore") as resp:
        print("[PASS] GET /api/weather/forecast?city=Indore:", resp.read().decode()[:150])

    # 5. Hourly (Mumbai)
    with urllib.request.urlopen("http://127.0.0.1:3007/api/weather/hourly?city=Mumbai") as resp:
        print("[PASS] GET /api/weather/hourly?city=Mumbai:", resp.read().decode()[:150])

    # 6. Search (Delhi)
    with urllib.request.urlopen("http://127.0.0.1:3007/api/weather/search?city=Delhi") as resp:
        print("[PASS] GET /api/weather/search?city=Delhi:", resp.read().decode()[:150])

    print("==================================================")
    print("ALL 6 LIVE WEATHER ENDPOINTS PASSED SUCCESSFULLY!")
    print("==================================================")

finally:
    proc.terminate()
    proc.wait()
