"""
scratch/verify_voice_and_chat_routing.py
Runtime verification testing:
1. source="voice" produces RESPONSE_CHUNK, TTS_DISPATCH, TTS_READY, FIRST_AUDIO_PLAYBACK_START, WS_TX speaking_start.
2. source="chat" produces RESPONSE_CHUNK without TTS_DISPATCH.
"""

import sys
sys.path.insert(0, ".")

import time
from conversation.command_router import CommandRouter

def run_verification():
    router = CommandRouter()
    print("=========================================================", flush=True)
    print("1. TESTING VOICE INPUT (source='voice')")
    print("=========================================================", flush=True)
    req_voice = "req_physical_voice_test_001"
    router.process_user_input("hello jarvis how are you", source="voice", request_id=req_voice)

    print("\n=========================================================", flush=True)
    print("2. TESTING CHAT INPUT (source='chat')")
    print("=========================================================", flush=True)
    req_chat = "req_physical_chat_test_002"
    router.process_user_input("what is Python?", source="chat", request_id=req_chat)

if __name__ == "__main__":
    run_verification()
