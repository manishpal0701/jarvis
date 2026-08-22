
import random

class StoryEngine:
    def __init__(self):
        pass

    def create_storyboard(self, clips, music, command):
        """
        Creates a timeline of clips based on the project type and music.
        """
        project_type = self._detect_project_type(command, clips)
        
        # Sort clips by quality and interesting features
        sorted_clips = sorted(clips, key=lambda x: x['quality_score'], reverse=True)
        
        timeline = []
        beats = music.get('beats', [])
        
        if not beats:
            # Simple 3-second cuts if no music
            current_time = 0
            for clip in sorted_clips:
                timeline.append({
                    "clip_path": clip['path'],
                    "start_time": 0,
                    "end_time": 3,
                    "timeline_pos": current_time
                })
                current_time += 3
        else:
            # Beat-matched editing
            current_time = 0
            beat_index = 0
            for clip in sorted_clips:
                if beat_index + 4 >= len(beats): break
                
                # Cut every 4 beats for steady pacing
                start_beat = beats[beat_index]
                end_beat = beats[beat_index + 4]
                duration = end_beat - start_beat
                
                timeline.append({
                    "clip_path": clip['path'],
                    "start_time": 0,
                    "end_time": duration,
                    "timeline_pos": current_time,
                    "effects": self._determine_effects(project_type, clip)
                })
                
                current_time += duration
                beat_index += 4
                
        return {
            "project_type": project_type,
            "timeline": timeline,
            "music": music
        }

    def _detect_project_type(self, command, clips):
        if "wedding" in command: return "wedding"
        if "vlog" in command: return "vlog"
        if "reels" in command or "shorts" in command: return "social_media"
        return "cinematic"

    def _determine_effects(self, project_type, clip):
        effects = []
        if project_type == "social_media":
            effects.append("speed_ramp")
            effects.append("zoom_in")
        elif project_type == "wedding":
            effects.append("color_grade_warm")
            effects.append("cross_dissolve")
        return effects
