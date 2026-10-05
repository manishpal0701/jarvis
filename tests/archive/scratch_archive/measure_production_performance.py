import sys
import os
import time
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import speech
speech.initialize()

from ai.ask_ollama import ask_ollama_streaming
from core.performance_profiler import PerformanceProfiler
from memory.memory_manager import MemoryManager
from conversation.intelligence.conversation_analyzer import ConversationAnalyzer

print("==================================================")
print("PRODUCTION PERFORMANCE CHECK")
print("==================================================")

# 1. Measure Memory Retrieval Latency
t_mem_start = time.perf_counter()
mem_mgr = MemoryManager()
memories = mem_mgr.retrieve_relevant("what is my current project?", limit=3, min_score=1.0)
t_mem_dur = time.perf_counter() - t_mem_start

# 2. Measure Conversation Analyzer Latency
t_conv_start = time.perf_counter()
analyzer = ConversationAnalyzer()
intel = analyzer.analyze_input("what is my current project?")
t_conv_dur = time.perf_counter() - t_conv_start

# 3. Measure Streaming Response End-to-End Latency
PerformanceProfiler.reset()
t_total_start = time.perf_counter()

print("\nExecuting streaming response: 'what is my current project?'")
resp = ask_ollama_streaming("what is my current project?", "Manish", "owner")

t_total_dur = time.perf_counter() - t_total_start

print("\n--------------------------------------------------")
print("EMPIRICAL PRODUCTION TIMINGS REPORT")
print("--------------------------------------------------")
print(f"Memory Retrieval Latency      : {t_mem_dur*1000:.2f} ms")
print(f"Conversation Intelligence     : {t_conv_dur*1000:.2f} ms")
print(f"Total Response Latency        : {t_total_dur:.3f} s")

# Extract profiler marks if available
marks = getattr(PerformanceProfiler._local, "marks", [])
mark_dict = {label: t for label, t in marks}

ollama_first = mark_dict.get("OLLAMA_FIRST_TOKEN", 0)
tts_first = mark_dict.get("TTS_FIRST_AUDIO", 0)
ollama_done = mark_dict.get("OLLAMA_COMPLETE", 0)

print(f"Ollama First-Token Latency    : {ollama_first:.3f} s")
print(f"Time to First Speech (Audio)  : {tts_first:.3f} s")
print(f"Ollama Generation Latency     : {(ollama_done - ollama_first):.3f} s" if (ollama_done and ollama_first) else f"Ollama Total Generation: {ollama_done:.3f} s")
print(f"Estimated Speech Recog (Google): ~1.00s - 1.50s (network STT roundtrip)")

speech.shutdown()
