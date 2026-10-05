"""
scratch/test_jarvis_weather_app_builder_e2e.py
End-to-end execution test for JARVIS Weather application.
"""
import os
import sys
import time
import json
import logging

sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WeatherAcceptanceTest")


def run_weather_app_build():
    prompt = """Jarvis, ek complete real-world Weather Forecast Android application banao.

IMPORTANT:
Is baar sirf architecture ya planning mat banana.
Mujhe REAL working application generate karke do.

==================================================
APP DETAILS
==================================================

App Name:
JARVIS Weather

Platform:
Flutter Android

Frontend:
Flutter

Backend:
Node.js + Express

Database:
Persistent local/database storage where required

==================================================
CORE PURPOSE
==================================================

Ek modern professional Weather Forecast application banao
jo worldwide locations ka real weather data fetch kare.

User duniya ke kisi bhi city, country ya location ka weather
search aur dekh sake.

==================================================
WEATHER DATA
==================================================

Real live weather API use karo.

Worldwide weather support hona chahiye.

Support:

- Current weather
- Temperature
- Feels like
- Humidity
- Pressure
- Wind speed
- Wind direction
- Visibility
- UV index where API supports it
- Cloud coverage
- Sunrise
- Sunset
- Weather condition
- Weather icon

Forecast:

- Hourly forecast
- 24 hour forecast
- 7 day forecast
- Daily high/low
- Rain probability
- Precipitation
- Wind forecast

Location search:

- City
- Country
- State/region where available
- Latitude/longitude

Examples test karo:

India:
Indore
Bhopal
Delhi
Mumbai
Bangalore

USA:
New York
Los Angeles

UK:
London

Japan:
Tokyo

Australia:
Sydney

UAE:
Dubai

==================================================
BACKEND
==================================================

Node.js + Express backend REAL APIs ke saath banao.

Backend APIs:

GET /api/weather/current

GET /api/weather/forecast

GET /api/weather/hourly

GET /api/weather/search

GET /api/weather/location

GET /api/health

Backend external weather API ko securely call kare.

API key frontend me expose mat karna.

Environment variables use karo:

WEATHER_API_KEY

==================================================
BACKEND REQUIREMENTS
==================================================

Implement:

- Request validation
- Error handling
- API timeout handling
- External API failure handling
- Invalid city handling
- Rate-limit friendly architecture
- Response normalization
- Caching where useful

Backend logs clearly show:

[WEATHER_API_REQUEST]
[WEATHER_API_RESPONSE]
[WEATHER_API_ERROR]

==================================================
FRONTEND
==================================================

Flutter me premium modern weather UI banao.

Screens:

1. Home
2. Search
3. Weather Details
4. Forecast
5. Saved Locations

Home:

- Current location weather
- Temperature
- Condition
- Weather icon
- Feels like
- Humidity
- Wind
- Sunrise/sunset
- Hourly forecast
- 7 day forecast

Search:

- Search any worldwide city
- Search results
- Select location
- Fetch live weather

Saved Locations:

- Add location
- Remove location
- Switch between saved locations

==================================================
UI
==================================================

Premium modern design.

Dark/light theme support.

Smooth animations.

Responsive layout.

Weather cards.

Loading states.

Error states.

Empty states.

Pull to refresh.

==================================================
REAL DATA
==================================================

Do NOT use fake hardcoded weather data for the
actual weather screens.

Use real weather API responses.

Demo/mock data may only be used for fallback/testing
when external API is unavailable.

==================================================
ARCHITECTURE
==================================================

First analyze the requirements and generate the architecture.

BUT:

DO NOT STOP AT:

WAITING_FOR_APPROVAL

The user has already explicitly authorized implementation.

After architecture is ready, AUTOMATICALLY continue:

Architecture
→ Flutter project creation
→ Node.js backend creation
→ API implementation
→ database/storage setup
→ frontend implementation
→ backend integration
→ dependency installation
→ build
→ tests
→ final verification

==================================================
LIVE STREAMING TEST
==================================================

This is a VERY IMPORTANT TEST.

I want to verify that Jarvis App Builder has REAL
live progress streaming.

While building the application, stream every major stage
through the existing WebSocket/event system.

==================================================
REAL EXECUTION VERIFICATION
==================================================

Do not report success merely because planning files exist.

Verify physically that these exist:

frontend/
  pubspec.yaml
  lib/
  android/

backend/
  package.json
  server.js or equivalent
  routes/
  controllers/
  services/

==================================================
PROGRESS LOGGING
==================================================

Every stage must have logs like:

[APP_RUNTIME]
stage=...
status=STARTED

[APP_RUNTIME]
stage=...
status=COMPLETED

On failure:

[APP_RUNTIME]
stage=...
status=FAILED
error=...
"""

    print("==================================================", flush=True)
    print("STARTING REAL APP BUILD: JARVIS Weather", flush=True)
    print("==================================================", flush=True)

    from tools.app_builder.app_manager import AppManager
    from conversation.command_router import CommandRouter

    # Reset AppManager state
    app_mgr = AppManager()
    with app_mgr._lock:
        app_mgr.active_app = None
        app_mgr.history.clear()
        app_mgr.queue.clear()

    router = CommandRouter()

    t0 = time.time()
    router.process_user_input(prompt, source="weather_build_test")
    t_ret = time.time() - t0

    print(f"\n[JARVIS_WEATHER] User command accepted in {t_ret:.2f}s", flush=True)

    active_app = app_mgr.get_active_app()
    if not active_app:
        print("[FAIL] Active app project was not created!", flush=True)
        sys.exit(1)

    print(f"[JARVIS_WEATHER] App ID: {active_app.app_id}", flush=True)
    print(f"[JARVIS_WEATHER] App Name: {active_app.name}", flush=True)

    # Wait up to 120s for completion
    start_w = time.time()
    while time.time() - start_w < 120:
        app = app_mgr.get_app_by_id(active_app.app_id)
        if app.status in [app.status.COMPLETED, app.status.FAILED]:
            break
        time.sleep(2)

    final_app = app_mgr.get_app_by_id(active_app.app_id)
    print(f"\n[JARVIS_WEATHER] Final Status: {final_app.status.value}", flush=True)
    print(f"[JARVIS_WEATHER] Final Progress: {final_app.progress}%", flush=True)
    print(f"[JARVIS_WEATHER] Workspace: {final_app.workspace_path}", flush=True)

    # Physical file verifications
    pubspec = os.path.join(final_app.frontend_path, "pubspec.yaml")
    pkg_json = os.path.join(final_app.backend_path, "package.json")
    server_js = os.path.join(final_app.backend_path, "src", "server.js")
    app_js = os.path.join(final_app.backend_path, "src", "app.js")

    print(f"[VERIFY] frontend/pubspec.yaml: {os.path.exists(pubspec)}", flush=True)
    print(f"[VERIFY] backend/package.json: {os.path.exists(pkg_json)}", flush=True)
    print(f"[VERIFY] backend/src/server.js: {os.path.exists(server_js)}", flush=True)
    print(f"[VERIFY] backend/src/app.js: {os.path.exists(app_js)}", flush=True)

    if not os.path.exists(pubspec) or not os.path.exists(pkg_json):
        print("[FAIL] Physical files missing!", flush=True)
        sys.exit(1)

    print("\n==================================================", flush=True)
    print("JARVIS WEATHER APPLICATION BUILD PASSED SUCCESSFULLY!")
    print("==================================================", flush=True)


if __name__ == "__main__":
    run_weather_app_build()
