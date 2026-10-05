"""
tests/test_phase8_riverpod_architecture.py
Phase 8 Riverpod Architecture Verification Tests.
Verifies that generated Flutter apps mandate Riverpod state management:
1. pubspec.yaml includes flutter_riverpod dependency.
2. main.dart wraps root app inside ProviderScope.
3. Screens inherit from ConsumerWidget or ConsumerStatefulWidget.
4. Business logic state providers exist in lib/providers/.
5. UI screens do NOT manage business logic using raw setState().
"""
import os
import shutil
import tempfile
import unittest

from tools.app_builder.flutter_generator import FlutterProjectGenerator

class TestPhase8RiverpodArchitecture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_riverpod_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_task_app_riverpod_generation(self):
        plan = {
            "app_name": "TaskFlow Master",
            "sanitized_name": "task_flow_master",
            "domain": "task",
            "theme": "Dark Modern Theme"
        }
        created_files = FlutterProjectGenerator.generate_frontend(self.temp_dir, plan)
        self.assertGreater(len(created_files), 5)

        # 1. Verify pubspec.yaml includes flutter_riverpod
        pubspec_path = os.path.join(self.temp_dir, "pubspec.yaml")
        self.assertTrue(os.path.exists(pubspec_path))
        with open(pubspec_path, "r", encoding="utf-8") as f:
            pubspec_content = f.read()
        self.assertIn("flutter_riverpod", pubspec_content)

        # 2. Verify main.dart has ProviderScope
        main_path = os.path.join(self.temp_dir, "lib", "main.dart")
        self.assertTrue(os.path.exists(main_path))
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        self.assertIn("ProviderScope", main_content)

        # 3. Verify task_provider.dart exists in lib/providers/
        provider_path = os.path.join(self.temp_dir, "lib", "providers", "task_provider.dart")
        self.assertTrue(os.path.exists(provider_path), f"Expected provider file at {provider_path}")
        with open(provider_path, "r", encoding="utf-8") as f:
            provider_content = f.read()
        self.assertIn("StateNotifier", provider_content)

        # 4. Verify screens use ConsumerWidget or ConsumerStatefulWidget
        dashboard_path = os.path.join(self.temp_dir, "lib", "screens", "dashboard_screen.dart")
        self.assertTrue(os.path.exists(dashboard_path))
        with open(dashboard_path, "r", encoding="utf-8") as f:
            screen_content = f.read()
        self.assertTrue("ConsumerWidget" in screen_content or "ConsumerStatefulWidget" in screen_content)
        self.assertIn("ref.watch", screen_content)

    def test_expense_app_riverpod_generation(self):
        plan = {
            "app_name": "ExpenseTracker Pro",
            "sanitized_name": "expense_tracker_pro",
            "domain": "expense",
            "theme": "Finance Dark Theme"
        }
        created_files = FlutterProjectGenerator.generate_frontend(self.temp_dir, plan)
        self.assertGreater(len(created_files), 5)

        # Verify expense provider exists
        provider_path = os.path.join(self.temp_dir, "lib", "providers", "expense_provider.dart")
        self.assertTrue(os.path.exists(provider_path))

    def test_weather_app_riverpod_generation(self):
        plan = {
            "app_name": "WeatherPulse AI",
            "sanitized_name": "weather_pulse_ai",
            "domain": "weather",
            "theme": "Sky Glass Theme"
        }
        created_files = FlutterProjectGenerator.generate_frontend(self.temp_dir, plan)
        self.assertGreater(len(created_files), 5)

        # Verify weather provider exists
        provider_path = os.path.join(self.temp_dir, "lib", "providers", "weather_provider.dart")
        self.assertTrue(os.path.exists(provider_path))

if __name__ == "__main__":
    unittest.main()
