import unittest
import os
import json
import shutil
import tempfile

from tools.app_builder.app_model import AppBrief, AppProject, AppState
from tools.app_builder.app_brief_merger import AppBriefMerger
from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer
from tools.app_builder.architecture_planner import ArchitecturePlanner
from tools.app_builder.app_manager import AppManager


class TestAppBriefIntegrity(unittest.TestCase):
    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()

        self.full_brief_input = (
            "Jarvis, ek complete Spotify-style Music Player Android app banao.\n\n"
            "App ka naam: JARVIS Music\n\n"
            "Purpose:\n"
            "Ek modern music streaming/player app jisme user different types ke music browse, search, play aur manage kar sake.\n\n"
            "Requirements:\n"
            "- Home Screen\n"
            "- Featured songs\n"
            "- Trending songs\n"
            "- Recently played\n"
            "- New releases\n"
            "- Popular artists\n"
            "- Popular albums\n"
            "- Mood-based sections\n"
            "- Playlists\n"
            "- Music categories\n"
            "- Search\n"
            "- Full music player\n"
            "- Mini player\n"
            "- Queue\n"
            "- Likes\n"
            "- Background playback\n"
            "- Demo music catalogue\n"
            "- Node.js + Express backend\n"
            "- Database persistence\n"
            "- Flutter Android frontend\n"
            "- Testing requirements"
        )

    def tearDown(self):
        self.app_mgr.reset()

    def test_1_canonical_full_brief_preserved(self):
        """1. Original full brief is preserved exactly in brief.full_text."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertEqual(brief.full_text, self.full_brief_input.strip())
        self.assertIn("Spotify-style Music Player", brief.full_text)

    def test_2_app_name_extracted_correctly(self):
        """2. App name == 'JARVIS Music'."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertEqual(brief.name, "JARVIS Music")

    def test_3_domain_detected_as_music(self):
        """3. Domain == 'music'."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        analyzed = AppRequirementsAnalyzer.analyze(brief)
        self.assertEqual(analyzed["domain"], "music")

    def test_4_backend_required_true(self):
        """4. backend_required == True."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        analyzed = AppRequirementsAnalyzer.analyze(brief)
        self.assertTrue(analyzed["needs_backend"])

    def test_5_backend_type_nodejs_express(self):
        """5. backend_type includes Node.js/Express."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        analyzed = AppRequirementsAnalyzer.analyze(brief)
        backend_reqs = " ".join(analyzed.get("backend_requirements", []))
        self.assertIn("Express.js", backend_reqs)

    def test_6_flutter_frontend_detected(self):
        """6. Flutter frontend is detected."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertIn("Flutter", brief.technology.get("frontend", "Flutter"))

    def test_7_music_requirements_preserved(self):
        """7. Music requirements are preserved."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertIn("Featured songs", brief.features)
        self.assertIn("Playlists", brief.features)

    def test_8_testing_requirements_preserved(self):
        """8. Testing requirements are preserved."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertIn("Testing requirements", brief.features)

    def test_9_architecture_planner_receives_complete_brief(self):
        """9. Architecture planner receives the complete brief."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        analyzed = AppRequirementsAnalyzer.analyze(brief)
        plan = ArchitecturePlanner.create_architecture_plan("app_test_123", analyzed)
        self.assertEqual(plan["app_metadata"]["app_name"], "JARVIS Music")
        self.assertEqual(plan["app_metadata"]["domain"], "music")

    def test_10_app_orchestrator_receives_complete_brief(self):
        """10. AppDevelopmentOrchestrator receives the complete brief."""
        project = self.app_mgr.create_app_project(initial_prompt=self.full_brief_input)
        self.assertEqual(project.name, "JARVIS Music")
        self.assertIn("JARVIS Music", project.brief.full_text)

    def test_11_no_feature_list_as_app_name(self):
        """11. No feature list is accidentally used as app name."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertFalse(brief.name.startswith("-"))
        self.assertNotIn("Artist name", brief.name)

    def test_12_no_truncation_occurs(self):
        """12. No truncation occurs."""
        brief = AppBrief()
        AppBriefMerger.merge_brief(brief, new_text=self.full_brief_input)
        self.assertEqual(len(brief.full_text), len(self.full_brief_input.strip()))

    def test_13_no_previous_project_brief_overwrites_new(self):
        """13. No previous project brief overwrites the new brief."""
        app1 = self.app_mgr.create_app_project(initial_prompt="App ka naam: Expense Tracker App")
        self.assertEqual(app1.name, "Expense Tracker App")

        self.app_mgr.reset()
        app2 = self.app_mgr.create_app_project(initial_prompt=self.full_brief_input)
        self.assertEqual(app2.name, "JARVIS Music")

    def test_14_persistence_recovery_preserves_complete_brief(self):
        """14. Persistence/recovery preserves the complete brief."""
        project = AppProject(name="JARVIS Music", brief=AppBrief(name="JARVIS Music", description=self.full_brief_input, full_text=self.full_brief_input))
        p_dict = project.to_dict()
        recovered = AppProject.from_dict(p_dict)
        self.assertEqual(recovered.brief.full_text, self.full_brief_input)
        self.assertEqual(recovered.name, "JARVIS Music")


if __name__ == "__main__":
    unittest.main()
