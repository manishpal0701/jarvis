"""
video_editing/reference/reference_mapper.py
Reference-to-User Asset Mapper & Beat-Sync Engine for Phase 5.5.
Maps Reference Style Profile + Cut Timeline onto User Asset Manifest,
aligning major cuts to detected music beats to produce an executable EditPlan.
"""

from typing import Dict, List, Any


class ReferenceMapper:
    """
    Maps reference editing language and cut structures onto user video/image assets,
    synchronizing cut transitions with music beat markers.
    """

    @classmethod
    def map_reference_to_assets(
        cls,
        ref_analysis: Dict[str, Any],
        style_profile: Dict[str, Any],
        asset_manifest: Dict[str, Any],
        music_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates beat-synchronized edit plan using user assets.
        """
        print("[BEAT_SYNC_START]", flush=True)

        user_videos = asset_manifest.get("video_assets", [])
        user_images = asset_manifest.get("image_assets", [])
        available_clips = user_videos + user_images

        if not available_clips:
            raise ValueError("No video or image assets found in user project folder.")

        # Reference shot structure & beat map
        ref_scenes = ref_analysis.get("rhythm", {}).get("scenes", [])
        beat_map = music_info.get("beat_map", [])
        music_track = music_info.get("selected_track")

        target_dur = ref_analysis.get("general", {}).get("duration", 30.0)
        avg_shot_dur = style_profile.get("avg_shot_duration", 2.0)

        operations = []
        timeline_t = 0.0
        clip_idx = 0

        beat_cut_count = 0

        # Construct segments matching reference shot count/durations
        for ref_idx, ref_shot in enumerate(ref_scenes):
            if timeline_t >= target_dur:
                break

            desired_dur = float(ref_shot.get("duration", avg_shot_dur))

            # Beat sync adjustment: align cut point to nearest beat timestamp
            if beat_map and style_profile.get("music_sync"):
                target_cut_t = timeline_t + desired_dur
                print(f"[BEAT_TARGET_SELECTED] target_time={target_cut_t:.2f}s", flush=True)

                # Find nearest beat in beat_map after target_cut_t
                future_beats = [b for b in beat_map if b > timeline_t + 0.5]
                if future_beats:
                    nearest_beat = min(future_beats, key=lambda b: abs(b - target_cut_t))
                    if abs(nearest_beat - target_cut_t) <= 1.5:
                        desired_dur = max(0.5, nearest_beat - timeline_t)
                        beat_cut_count += 1
                        print(f"[BEAT_CUT_APPLIED] beat_time={nearest_beat:.2f}s duration={desired_dur:.2f}s", flush=True)

            # Pick next asset in round-robin / quality order
            asset_item = available_clips[clip_idx % len(available_clips)]
            clip_idx += 1

            asset_path = asset_item.get("file_path")
            asset_type = asset_item.get("type", "video")
            asset_name = asset_item.get("filename")

            if asset_type == "video":
                asset_max_dur = asset_item.get("duration", 5.0)
                in_t = 0.0
                out_t = min(asset_max_dur, in_t + desired_dur)
                dur_used = out_t - in_t
            else:
                # Still image clip segment
                in_t = 0.0
                out_t = desired_dur
                dur_used = desired_dur

            op = {
                "step": len(operations) + 1,
                "asset": asset_name,
                "clip_path": asset_path,
                "asset_type": asset_type,
                "filename": asset_name,
                "in": round(in_t, 2),
                "out": round(out_t, 2),
                "source_start": round(in_t, 2),
                "source_end": round(out_t, 2),
                "timeline_pos": round(timeline_t, 2),
                "timeline_start": round(timeline_t, 2),
                "timeline_end": round(timeline_t + dur_used, 2),
                "duration": round(dur_used, 2),
                "speed": 1.0 if not style_profile.get("speed_ramps") else (1.2 if ref_idx % 2 == 0 else 0.9),
                "transition": style_profile.get("transition_style", "hard_cut") if ref_idx > 0 else "cut",
                "effect": "push_in" if ref_idx % 3 == 0 else "none",
                "color_treatment": style_profile.get("color_style", "cinematic_warm"),
                "beat_sync": bool(beat_cut_count > 0)
            }
            operations.append(op)
            timeline_t += dur_used

        print(f"[BEAT_SYNC_COMPLETE] total_cuts={len(operations)} beat_synced_cuts={beat_cut_count}", flush=True)

        edit_plan = {
            "edit_goal": f"Reference-Based Edit ({style_profile.get('pace')} pace)",
            "reference_file": ref_analysis.get("filename"),
            "target_duration": round(timeline_t, 2),
            "aspect_ratio": ref_analysis.get("general", {}).get("aspect_ratio", "9:16"),
            "style_profile": style_profile,
            "music_track": music_track.get("filename") if music_track else None,
            "music_path": music_track.get("file_path") if music_track else None,
            "bpm": music_info.get("bpm", 120.0),
            "total_clips_used": len(operations),
            "beat_synced_cuts": beat_cut_count,
            "operations": operations
        }

        return edit_plan
