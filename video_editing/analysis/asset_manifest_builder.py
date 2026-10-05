"""
video_editing/analysis/asset_manifest_builder.py
Asset Discovery Manifest Builder for Phase 5.5 Reference-Based Video Editing.
Scans project folder recursively for Videos, Images, Music, and SFX assets,
extracting real file metadata and producing structured counts.
"""

import os
from typing import Dict, List, Any
from video_editing.analysis.media_analyzer import analyze_media

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}


class AssetManifestBuilder:
    """
    Scans local project directories to build an asset manifest categorizing
    Videos, Images, Music tracks, and SFX assets.
    """

    @classmethod
    def build_manifest(cls, folder_path: str) -> Dict[str, Any]:
        """
        Recursively scans directory and builds structured asset manifest.
        """
        if not folder_path or not os.path.isdir(folder_path):
            return {
                "folder_path": folder_path,
                "video_assets": [],
                "image_assets": [],
                "music_assets": [],
                "sfx_assets": [],
                "summary": {
                    "video_count": 0,
                    "image_count": 0,
                    "music_count": 0,
                    "sfx_count": 0
                }
            }

        abs_folder = os.path.abspath(folder_path)
        video_assets: List[Dict[str, Any]] = []
        image_assets: List[Dict[str, Any]] = []
        music_assets: List[Dict[str, Any]] = []
        sfx_assets: List[Dict[str, Any]] = []

        for root_dir, _, files in os.walk(abs_folder):
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                full_path = os.path.abspath(os.path.join(root_dir, file_name))
                try:
                    file_size = os.path.getsize(full_path)
                except Exception:
                    file_size = 0

                if ext in VIDEO_EXTENSIONS:
                    meta = analyze_media(full_path)
                    video_assets.append({
                        "type": "video",
                        "file_path": full_path,
                        "filename": file_name,
                        "extension": ext,
                        "duration": meta.get("duration", 0.0),
                        "resolution": meta.get("resolution", "UNKNOWN"),
                        "fps": meta.get("fps", 0.0),
                        "codec": meta.get("video_codec", "UNKNOWN"),
                        "audio_presence": meta.get("audio_presence", False),
                        "file_size": file_size
                    })

                elif ext in IMAGE_EXTENSIONS:
                    meta = analyze_media(full_path)
                    image_assets.append({
                        "type": "image",
                        "file_path": full_path,
                        "filename": file_name,
                        "extension": ext,
                        "resolution": meta.get("resolution", "UNKNOWN"),
                        "width": meta.get("width", 0),
                        "height": meta.get("height", 0),
                        "file_size": file_size
                    })

                elif ext in AUDIO_EXTENSIONS:
                    # Categorize audio as music or SFX based on duration/filename keywords
                    meta = analyze_media(full_path)
                    aud_meta = meta.get("audio_analysis", {})
                    dur = aud_meta.get("audio_duration") or meta.get("duration", 0.0)
                    if not isinstance(dur, (int, float)):
                        dur = 0.0

                    is_sfx_name = any(kw in file_name.lower() for kw in ["sfx", "sound_effect", "whoosh", "hit", "pop", "riser"])
                    if (dur > 0 and dur <= 10.0) or is_sfx_name:
                        sfx_assets.append({
                            "type": "sfx",
                            "file_path": full_path,
                            "filename": file_name,
                            "extension": ext,
                            "duration": round(float(dur), 2),
                            "file_size": file_size
                        })
                    else:
                        music_assets.append({
                            "type": "music",
                            "file_path": full_path,
                            "filename": file_name,
                            "extension": ext,
                            "duration": round(float(dur), 2),
                            "bpm": aud_meta.get("bpm", "UNKNOWN"),
                            "beat_timestamps": aud_meta.get("beat_timestamps", []),
                            "file_size": file_size
                        })

        summary = {
            "video_count": len(video_assets),
            "image_count": len(image_assets),
            "music_count": len(music_assets),
            "sfx_count": len(sfx_assets)
        }

        print(
            f"[ASSET_DISCOVERY]\n"
            f"folder={abs_folder}\n"
            f"videos={summary['video_count']} "
            f"images={summary['image_count']} "
            f"music={summary['music_count']} "
            f"sfx={summary['sfx_count']}",
            flush=True
        )

        return {
            "folder_path": abs_folder,
            "video_assets": video_assets,
            "image_assets": image_assets,
            "music_assets": music_assets,
            "sfx_assets": sfx_assets,
            "summary": summary
        }
