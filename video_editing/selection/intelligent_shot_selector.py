"""
video_editing/selection/intelligent_shot_selector.py
Phase 7 Multi-Factor Intelligent Shot Selector Engine.
Calculates 7-factor composite scores (Reference Match, Visual Quality, Motion Match,
Composition Match, Music Sync, Duration Fit, Story Relevance) and applies usage penalties
to select optimal candidate clips for each timeline section.
"""

from typing import Dict, List, Any


class IntelligentShotSelector:
    """
    Evaluates and selects candidate user video/image assets for structural timeline segments.
    """

    @classmethod
    def select_shots_for_template(
        cls,
        timeline_template: List[Dict[str, Any]],
        asset_manifest: Dict[str, Any],
        music_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Selects highest-scoring user assets for each template segment.
        """
        print("[SHOT_SELECTION_START]", flush=True)

        user_videos = asset_manifest.get("video_assets", [])
        user_images = asset_manifest.get("image_assets", [])
        all_assets = user_videos + user_images

        if not all_assets:
            raise ValueError("No video or image assets available in project folder.")

        selected_assignments = []
        usage_counts: Dict[str, int] = {}

        print(f"[SHOT_RANKING_START] candidates={len(all_assets)} segments={len(timeline_template)}", flush=True)

        for seg in timeline_template:
            seg_id = seg.get("segment_id", seg.get("shot_id", "shot_1"))
            section_name = seg.get("section", seg.get("pacing_phase", "body"))
            req_dur = float(seg.get("target_duration", 2.0))

            best_asset = None
            best_score = -1.0
            rejected_candidates = []

            for asset in all_assets:
                path = asset.get("file_path")
                filename = asset.get("filename")

                ref_match_score = float(asset.get("ref_match", 85.0 if asset.get("type") == "video" else 65.0))
                quality_score = float(asset.get("visual_quality", 90.0 if asset.get("file_size", 0) > 100000 else 70.0))
                motion_score = float(asset.get("motion_match", 80.0 if asset.get("type") == "video" else 40.0))
                comp_score = float(asset.get("composition_match", 80.0))
                music_sync_score = 90.0 if music_info.get("selected_track") else 50.0

                asset_dur = float(asset.get("duration", 5.0))
                duration_fit_score = 100.0 if asset_dur >= req_dur else (asset_dur / max(0.1, req_dur)) * 100.0
                story_rel_score = 85.0

                used_count = usage_counts.get(path, 0)
                reuse_penalty = used_count * 25.0

                # Phase 7 7-factor composite formula
                total_score = (
                    0.25 * ref_match_score +
                    0.20 * quality_score +
                    0.15 * motion_score +
                    0.15 * comp_score +
                    0.10 * music_sync_score +
                    0.10 * duration_fit_score +
                    0.05 * story_rel_score -
                    reuse_penalty
                )

                print(
                    f"[SHOT_CANDIDATE] section={section_name} candidate='{filename}' "
                    f"score={total_score:.1f} reuse_count={used_count}",
                    flush=True
                )

                if total_score > best_score:
                    if best_asset:
                        rejected_candidates.append(best_asset.get("filename"))
                    best_score = total_score
                    best_asset = asset
                else:
                    rejected_candidates.append(filename)

            if not best_asset:
                best_asset = all_assets[0]

            for rej in rejected_candidates[:2]:
                print(f"[SHOT_REJECTED] section={section_name} candidate='{rej}' reason=LOWER_COMPOSITE_SCORE", flush=True)

            path = best_asset.get("file_path")
            usage_counts[path] = usage_counts.get(path, 0) + 1

            assignment = {
                "segment_id": seg_id,
                "asset_path": path,
                "filename": best_asset.get("filename"),
                "asset_type": best_asset.get("type", "video"),
                "target_duration": req_dur,
                "score": round(best_score, 1),
                "pacing_phase": section_name
            }

            print(
                f"[SHOT_SELECTED] section={section_name} asset='{assignment['filename']}' "
                f"score={assignment['score']}",
                flush=True
            )
            selected_assignments.append(assignment)

        print(f"[SHOT_SELECTION_COMPLETE] total_selected={len(selected_assignments)}", flush=True)
        return selected_assignments
