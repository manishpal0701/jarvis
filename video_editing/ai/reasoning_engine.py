
import random

class ReasoningEngine:
    def __init__(self):
        self.decision_pool = {
            "selection": [
                "I selected this clip because it has the highest emotional impact and stability.",
                "This shot provides the perfect establishing context for the project.",
                "The lighting in this frame is superior, creating a professional look.",
                "I'm using this clip to bridge the transition between the intro and build-up."
            ],
            "rejection": [
                "I removed this clip because the motion blur exceeded professional thresholds.",
                "This clip was rejected due to inconsistent white balance.",
                "Excluded this segment to maintain a faster narrative pace.",
                "This shot was out of focus, which would lower the perceived quality of the edit."
            ],
            "transition": [
                "Using a whip-pan here to match the dynamic camera movement.",
                "I selected this transition to synchronize with the tempo of the music.",
                "Applying a mask transition for a seamless cinematic flow.",
                "A cross-dissolve is used here to match the emotional tone of the scene."
            ],
            "grading": [
                "Applying warm tones because luxury real estate visuals perform better with high-end grading.",
                "Applying a high-contrast teal and orange look for that modern travel vlog aesthetic.",
                "Vibrant grading applied to match the energetic mood of the background score.",
                "Natural color correction implemented to preserve the authenticity of the moment."
            ]
        }

    def get_reason(self, category):
        return random.choice(self.decision_pool.get(category, ["Ensuring cinematic consistency for this cut."]))
