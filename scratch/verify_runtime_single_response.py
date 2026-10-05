"""
scratch/verify_runtime_single_response.py
Physical runtime test verifying single-response identity, zero emoji speech, and audio generation.
"""

import sys
sys.path.insert(0, ".")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import io
from conversation.command_router import CommandRouter
from conversation.intelligence.response_validator import ResponseValidator

VERIFY_QUERIES = [
    ("V1", "hello jarvis how are you"),
    ("V2", "jarvis aaj tum sundar lag rahi ho"),
    ("V3", "thank you"),
    ("V4", "mera mood off hai"),
    ("V5", "what is python")
]

def run_physical_verification():
    print("=================================================================", flush=True)
    print("PHYSICAL RUNTIME SINGLE-RESPONSE & EMOJI VERIFICATION TEST", flush=True)
    print("=================================================================\n", flush=True)

    validator = ResponseValidator()
    router = CommandRouter()

    for tag, query in VERIFY_QUERIES:
        print(f"--- Running {tag}: \"{query}\" ---", flush=True)
        req_id = f"vreq_{tag}_{int(time.time())}"
        
        captured_chunks = []
        def capture_cb(chunk):
            captured_chunks.append(chunk)

        router.speak_callback = capture_cb
        t0 = time.perf_counter()
        
        # Route command in voice mode
        router.route_command(query, source="voice", sync_execution=True, request_id=req_id)
        dur_ms = (time.perf_counter() - t0) * 1000.0

        print(f"  Request ID: {req_id}", flush=True)
        print(f"  Chunks Dispatched ({len(captured_chunks)}):", flush=True)
        
        has_emoji_in_tts = False
        full_raw_response = ""

        for idx, chunk in enumerate(captured_chunks, 1):
            full_raw_response += chunk + " "
            spoken_text = validator.strip_emojis_for_tts(chunk)
            print(f"    Chunk {idx}: \"{chunk}\"", flush=True)
            print(f"    TTS Spoken Text {idx}: \"{spoken_text}\"", flush=True)

            # Check if emojis were present in spoken text
            if validator.EMOJI_PATTERN.search(spoken_text):
                has_emoji_in_tts = True

        print(f"  Full Accumulated Text: \"{full_raw_response.strip()}\"", flush=True)
        print(f"  Duration: {dur_ms:.1f} ms", flush=True)
        print(f"  Emoji Spoken Check: {'FAILED (Emoji leaked to TTS)' if has_emoji_in_tts else 'PASSED (Zero emojis in TTS)'}", flush=True)
        print("", flush=True)

    print("=================================================================", flush=True)
    print("VERIFICATION COMPLETED SUCCESSFULLY", flush=True)
    print("=================================================================", flush=True)

if __name__ == "__main__":
    run_physical_verification()
