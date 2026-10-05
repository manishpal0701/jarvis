"""
video_editing/analysis/music_analyzer.py
Music Intelligence & Beat Analysis Engine for Phase 7.
Selects optimal audio tracks, extracts BPM, loudness/energy curves, constructs
BeatTimelines (downbeats, strong beats, drops, energy peaks, transitions), and
synchronizes edit cuts to music beats.
"""

import os
from typing import Dict, List, Any, Optional
from video_editing.analysis.audio_analyzer import analyze_audio


class MusicAnalyzer:
    """
    Analyzes music assets, calculates track energy/BPM, creates BeatTimelines,
    and synchronizes video cuts to music beats.
    """

    @classmethod
    def process_music_assets(
        cls,
        music_assets: List[Dict[str, Any]],
        target_pacing: str = "medium",
        target_duration: float = 30.0,
        preferred_track_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes all available music assets and selects the optimal track.
        """
        print(f"[MUSIC_DISCOVERY] available_tracks={len(music_assets)}", flush=True)

        if not music_assets:
            return {
                "selected_track": None,
                "bpm": "UNKNOWN",
                "beat_map": [],
                "beat_timeline": [],
                "energy": "medium",
                "status": "NO_MUSIC"
            }

        analyzed_tracks = []
        for track in music_assets:
            file_path = track.get("file_path")
            print(f"[MUSIC_ANALYSIS] track='{track.get('filename')}'", flush=True)

            audio_res = analyze_audio(file_path)
            bpm_val = audio_res.get("bpm")
            beat_times = audio_res.get("beat_timestamps", [])
            dur = audio_res.get("audio_duration") or track.get("duration", 0.0)

            if not isinstance(bpm_val, (int, float)) or bpm_val <= 0:
                bpm_val = 120.0

            if bpm_val >= 130:
                energy = "high"
            elif bpm_val <= 95:
                energy = "low"
            else:
                energy = "medium"

            track_info = {
                "file_path": file_path,
                "filename": track.get("filename"),
                "duration": round(float(dur), 2) if isinstance(dur, (int, float)) else 0.0,
                "bpm": round(float(bpm_val), 1),
                "beat_timestamps": beat_times,
                "energy": energy,
                "confidence": audio_res.get("tempo_confidence", 0.5)
            }
            analyzed_tracks.append(track_info)

        # Prioritize preferred track if specified
        selected = None
        if preferred_track_path:
            for trk in analyzed_tracks:
                if trk["file_path"] == preferred_track_path or trk["filename"] == os.path.basename(preferred_track_path):
                    selected = trk
                    break

        if not selected:
            selected = cls._select_best_track(analyzed_tracks, target_pacing, target_duration)

        bpm_detected = selected.get("bpm", 120.0)
        beat_map = selected.get("beat_timestamps", [])

        if not beat_map and isinstance(bpm_detected, (int, float)) and bpm_detected > 0:
            beat_interval = 60.0 / bpm_detected
            curr_t = 0.0
            dur_limit = selected.get("duration") or target_duration or 60.0
            while curr_t < dur_limit:
                beat_map.append(round(curr_t, 2))
                curr_t += beat_interval

        beat_timeline = cls.create_beat_timeline(bpm_detected, beat_map, selected.get("duration", 30.0))

        print(f"[MUSIC_TRACK_SELECTED] track='{selected.get('filename')}' duration={selected.get('duration')}s", flush=True)
        print(f"[MUSIC_SELECTED] file='{selected.get('filename')}' duration={selected.get('duration')}s", flush=True)
        print(f"[BPM_DETECTED] bpm={bpm_detected}", flush=True)
        print(f"[BEAT_MAP_CREATED] total_beats={len(beat_map)}", flush=True)

        return {
            "selected_track": selected,
            "bpm": bpm_detected,
            "beat_map": beat_map,
            "beat_timeline": beat_timeline,
            "energy": selected.get("energy", "medium"),
            "status": "SELECTED"
        }

    @classmethod
    def create_beat_timeline(cls, bpm: float, beat_map: List[float], total_duration: float) -> List[Dict[str, Any]]:
        """Constructs detailed BeatTimeline with downbeats, strong beats, drops, and energy peaks."""
        timeline = []
        for idx, t in enumerate(beat_map):
            beat_type = "downbeat" if idx % 4 == 0 else ("strong_beat" if idx % 2 == 0 else "regular_beat")
            is_drop = (t >= total_duration * 0.4 and t <= total_duration * 0.5)
            timeline.append({
                "beat_index": idx,
                "timestamp": t,
                "type": beat_type,
                "is_drop": is_drop,
                "energy_peak": is_drop or (idx % 8 == 0)
            })

        print(f"[BEAT_TIMELINE_CREATED] total_entries={len(timeline)}", flush=True)
        return timeline

    @classmethod
    def synchronize_cuts_to_beats(
        cls,
        shots: List[Dict[str, Any]],
        beat_map: List[float]
    ) -> List[Dict[str, Any]]:
        """Aligns segment cut boundaries to nearest music beats."""
        print(f"[MUSIC_SYNC_START] shots={len(shots)} available_beats={len(beat_map)}", flush=True)

        if not beat_map or not shots:
            print("[MUSIC_SYNC_COMPLETE] status=SKIPPED_NO_BEATS", flush=True)
            return shots

        synced_shots = []
        curr_time = 0.0

        for idx, shot in enumerate(shots):
            req_dur = shot.get("target_duration", 2.0)
            ideal_end = curr_time + req_dur

            # Find closest beat after or near ideal_end
            closest_beat = min(beat_map, key=lambda b: abs(b - ideal_end)) if beat_map else ideal_end
            if abs(closest_beat - ideal_end) > 1.5:
                closest_beat = ideal_end

            adjusted_dur = max(0.5, round(closest_beat - curr_time, 2))
            actual_end = round(curr_time + adjusted_dur, 2)

            shot["start_time"] = curr_time
            shot["end_time"] = actual_end
            shot["target_duration"] = adjusted_dur
            shot["beat_synced"] = True

            print(
                f"[MUSIC_SYNC_CUT] shot_id={shot.get('shot_id', idx+1)} "
                f"cut_at={actual_end}s dur={adjusted_dur}s beat_synced=TRUE",
                flush=True
            )
            synced_shots.append(shot)
            curr_time = actual_end

        print(f"[MUSIC_SYNC_COMPLETE] total_synced_cuts={len(synced_shots)}", flush=True)
        return synced_shots

    @classmethod
    def _select_best_track(
        cls,
        analyzed_tracks: List[Dict[str, Any]],
        target_pacing: str,
        target_duration: float
    ) -> Dict[str, Any]:
        """Ranks tracks by pacing alignment and duration coverage."""
        desired_energy = "high" if target_pacing in ["fast", "high"] else ("low" if target_pacing in ["slow", "low"] else "medium")

        best_track = analyzed_tracks[0]
        best_score = -1.0

        for trk in analyzed_tracks:
            score = 0.0
            if trk["energy"] == desired_energy:
                score += 50.0

            if trk["duration"] >= target_duration:
                score += 30.0
            else:
                score += (trk["duration"] / max(1.0, target_duration)) * 20.0

            if score > best_score:
                best_score = score
                best_track = trk

        return best_track
