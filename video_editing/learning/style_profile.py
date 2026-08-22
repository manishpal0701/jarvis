
import json
import os

class StyleLearningEngine:
    def __init__(self):
        self.profile_path = os.path.join(os.getcwd(), "video_editing", "memory", "user_style.json")
        self.style = self._load_style()

    def _load_style(self):
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r") as f:
                return json.load(f)
        return {
            "favorite_transitions": ["cross_dissolve"],
            "favorite_fonts": ["Inter-Bold"],
            "pacing": "cinematic",
            "preferred_software": "premiere"
        }

    def learn_from_edit(self, timeline):
        """
        Updates the profile based on user's manual adjustments.
        In production, this would compare AI timeline vs User's exported XML.
        """
        pass

    def get_style(self):
        return self.style
