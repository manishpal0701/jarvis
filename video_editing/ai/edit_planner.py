"""
video_editing/ai/edit_planner.py
Ollama Storytelling Engine for Jarvis Video Editor.
Translates user request and media analysis into a validated, structured JSON edit plan.
"""

import json
import re
from ai.ai_response_manager import AIResponseManager, LLMTimeoutException
from video_editing.ai.edit_plan_schema import validate_edit_plan


SYSTEM_PROMPT = """You are the Jarvis AI Video Edit Planner.
Your job is to convert the user's video editing request and the provided media & audio metadata into a STRICT JSON edit plan.

SUPPORTED EDITING STYLES:
- cinematic (Hook -> Establishing -> Slow Build -> Peak -> Fade)
- travel_reel (Fast Hook -> Action Cuts -> Beat Sync -> Payoff -> Outro)
- instagram_reel (9:16 vertical, rapid beat-matched cuts, high energy)
- youtube_video (Intro Hook -> Content Sections -> Highlights -> Call to Action)
- product_promo (Feature Showcase -> Closeups -> Benefits -> Brand End)
- birthday_montage (Emotional Intro -> Fun Moments -> Memory Peak -> Warm Ending)
- corporate_video (Executive Intro -> Achievements -> Operations -> Professional Outro)

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with a single valid JSON object with NO extra text before or after.
Do NOT output markdown formatting around the JSON unless it is a standard ```json ... ``` code block.

JSON SCHEMA REQUIREMENT:
{
  "edit_goal": "<short_description>",
  "target_duration": <number_seconds>,
  "aspect_ratio": "<9:16|16:9|1:1>",
  "style": "<cinematic|travel_reel|instagram_reel|youtube_video|product_promo|birthday_montage|corporate_video>",
  "scenes": [
    {
      "source_scene_id": "<scene_id>",
      "source_start": <start_time>,
      "source_end": <end_time>,
      "timeline_start": <timeline_start_time>,
      "reason": "<explanation>"
    }
  ],
  "operations": [
    {
      "type": "<insert|overwrite|move|trim|split|delete|place_video|place_audio|transition|visual_effect|align_audio_beat|move_audio|trim_audio|delete_audio>",
      "source_scene_id": "<scene_id>",
      "track_type": "<video|audio>",
      "track_index": 0,
      "in": <in_timestamp>,
      "out": <out_timestamp>,
      "timeline_pos": <position_timestamp>,
      "transition_type": "<cut|dissolve|fade|crossfade>",
      "duration": <transition_duration_seconds>,
      "effect_name": "<brightness|contrast|opacity|color_balance|saturation>",
      "value": <numeric_effect_value>,
      "beat_time": <beat_timestamp_seconds>
    }
  ]
}

CRITICAL RULES:
1. 'type' MUST be one of: insert, overwrite, move, trim, split, delete, place_video, place_audio, transition, visual_effect, align_audio_beat, move_audio, trim_audio, delete_audio.
2. All timestamps ('in', 'out', 'timeline_pos', 'split_time', 'target_duration', 'beat_time', 'duration') MUST be non-negative numbers.
3. Every 'source_scene_id' MUST exist in the provided SCENES list.
4. 'out' MUST be strictly greater than 'in', and 'out' cannot exceed the total media duration.
5. If beat timestamps are provided, align cut timestamps and 'timeline_pos' to beat timestamps where appropriate.
"""


def generate_edit_plan(user_request: str, media_analysis: dict, max_retries: int = 1) -> dict:
    """
    Generates a validated edit plan JSON using Ollama.
    Returns:
      Success: {"success": True, "plan": {...}, "error": None}
      Failure: {"success": False, "plan": None, "error": {"code": "...", "message": "..."}}
    """
    if not user_request or not isinstance(user_request, str):
        return _err("INVALID_REQUEST", "user_request must be a non-empty string.")

    if not media_analysis or not isinstance(media_analysis, dict):
        return _err("INVALID_MEDIA_ANALYSIS", "media_analysis must be a valid metadata dict.")

    # Format user prompt payload
    metadata = media_analysis.get("metadata", media_analysis)
    scenes = media_analysis.get("scenes", [])
    audio_analysis = metadata.get("audio_analysis", {})

    prompt_payload = {
        "user_request": user_request,
        "media_metadata": {
            "duration": metadata.get("duration", 0.0),
            "resolution": metadata.get("resolution", "UNKNOWN"),
            "fps": metadata.get("fps", 30.0),
            "video_codec": metadata.get("video_codec", "UNKNOWN"),
            "audio_presence": metadata.get("audio_presence", False)
        },
        "audio_analysis": {
            "bpm": audio_analysis.get("bpm", "UNKNOWN"),
            "beat_timestamps": audio_analysis.get("beat_timestamps", []),
            "tempo_confidence": audio_analysis.get("tempo_confidence", "NOT_AVAILABLE"),
            "audio_duration": audio_analysis.get("audio_duration", "NOT_AVAILABLE")
        },
        "scenes": [
            {
                "scene_id": sc.get("scene_id"),
                "start": sc.get("start"),
                "end": sc.get("end"),
                "duration": sc.get("duration")
            }
            for sc in scenes if isinstance(sc, dict)
        ]
    }

    user_message = json.dumps(prompt_payload, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate a video edit plan for this input:\n{user_message}"}
    ]

    ai_manager = AIResponseManager()

    for attempt in range(max_retries + 1):
        try:
            raw_response = ai_manager.generate_response(
                messages=messages,
                keep_alive=-1,
                timeout=5.0,
                think=False
            )
        except LLMTimeoutException as te:
            return _err("OLLAMA_TIMEOUT", str(te))
        except Exception as e:
            return _err("OLLAMA_UNAVAILABLE", f"Could not reach Ollama LLM service: {e}")

        # Parse JSON output
        parsed_plan = _parse_json_from_response(raw_response)
        if not parsed_plan:
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({"role": "user", "content": "Your response was not valid JSON. Return ONLY the strict JSON object."})
                continue
            return _err("INVALID_JSON_OUTPUT", f"Ollama failed to return valid JSON. Raw output: {raw_response[:200]}")

        # Validate schema
        valid, val_res = validate_edit_plan(parsed_plan, media_metadata=metadata, scene_list=scenes)
        if valid:
            return {
                "success": True,
                "plan": parsed_plan,
                "error": None
            }
        else:
            if attempt < max_retries:
                err_msg = val_res.get("error", {}).get("message", "Schema error")
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({"role": "user", "content": f"The edit plan failed schema validation: {err_msg}. Please fix and return ONLY valid JSON."})
                continue
            return val_res

    return _err("PLAN_GENERATION_FAILED", "Failed to generate valid edit plan after retries.")


def _parse_json_from_response(text: str) -> dict | None:
    """Extract and parse JSON dict from response string."""
    if not text:
        return None

    # Try direct parse
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Try regex extraction of ```json ... ``` or { ... }
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        try:
            data = json.loads(code_block_match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        try:
            data = json.loads(brace_match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


def _err(code: str, message: str) -> dict:
    return {
        "success": False,
        "plan": None,
        "error": {
            "code": code,
            "message": message
        }
    }
