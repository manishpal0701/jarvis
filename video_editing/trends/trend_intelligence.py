
class TrendIntelligenceEngine:
    def __init__(self):
        pass

    def get_latest_trends(self, platform="instagram"):
        """
        Returns a dictionary of current popular editing styles.
        """
        trends = {
            "instagram": {
                "hook_duration": 0.8,
                "transition": "mask_zoom",
                "color_preset": "teal_orange",
                "fonts": "The-Outfit"
            },
            "youtube_shorts": {
                "hook_duration": 1.2,
                "transition": "none",
                "color_preset": "vibrant",
                "fonts": "Montserrat-Bold"
            }
        }
        return trends.get(platform, trends["instagram"])
