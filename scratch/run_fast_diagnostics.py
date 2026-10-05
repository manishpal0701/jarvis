import sys
import os
import time
import json
import urllib.request
import psutil
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import speech
# Mock speech.speak to avoid pyttsx3/audio device blocking during diagnostic benchmarking
speech.speak = lambda text, wait=False, speech_id=None, request_id=None: "C:/tmp/mock_audio.mp3"

from ai.ask_ollama import ask_ollama_streaming, _build_pipeline
from ai.ai_response_manager import AIResponseManager, CONVERSATION_OPTIONS, MODEL_NAME
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

def get_ollama_ps():
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/ps", timeout=2.0)
        data = json.loads(req.read())
        return data.get("models", [])
    except Exception as e:
        return []

def get_system_telemetry():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    vmem = psutil.virtual_memory()
    ollama_cpu = None
    ollama_ram_mb = None
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
        try:
            if 'ollama' in proc.info['name'].lower():
                ollama_cpu = proc.info['cpu_percent']
                ollama_ram_mb = proc.info['memory_info'].rss / (1024 * 1024)
                break
        except Exception:
            pass
    return {
        "system_cpu_percent": cpu_percent,
        "ram_percent": vmem.percent,
        "available_ram_mb": vmem.available / (1024 * 1024),
        "ollama_cpu_percent": ollama_cpu,
        "ollama_ram_mb": ollama_ram_mb
    }

print("\n=======================================================")
print("JARVIS PHASE 2 DIAGNOSTIC TELEMETRY RUNNER")
print("=======================================================\n", flush=True)

# -------------------------------------------------------------------
# 1. VERIFY DUPLICATE REQUESTS & PROMPT METADATA FOR SINGLE VOICE COMMAND
# -------------------------------------------------------------------
print("--- TEST 1: SINGLE COMMAND DUPLICATE AUDIT ---", flush=True)
cmd = "Jarvis, explain Python in three sentences in simple Hinglish."
req_id = "phase2_diag_cmd_1"

state_machine = StateMachine()
timeout_manager = TimeoutManager(10.0)
speech_coordinator = SpeechCoordinator(state_machine, timeout_manager)

request_tracker = []
original_gen = AIResponseManager.generate_response_streaming

def tracked_gen(self, messages, sentence_callback, **kwargs):
    t_now = datetime.now().isoformat()
    req_info = {
        "timestamp": t_now,
        "messages_count": len(messages),
        "model": kwargs.get("model_name") or MODEL_NAME,
        "options": kwargs.get("options"),
        "keep_alive": kwargs.get("keep_alive"),
        "think": kwargs.get("think")
    }
    request_tracker.append(req_info)
    print(f"[OLLAMA_TRACE] request_sent timestamp={t_now}", flush=True)
    print(f"[OLLAMA_TRACE] model={req_info['model']} keep_alive={req_info['keep_alive']} num_ctx={req_info['options'].get('num_ctx')} num_predict={req_info['options'].get('num_predict')} think={req_info['think']}", flush=True)
    return original_gen(self, messages, sentence_callback, **kwargs)

router = CommandRouter(speech_coordinator=speech_coordinator)
setattr(AIResponseManager, 'generate_response_streaming', tracked_gen)

start_t = time.perf_counter()
router.process_user_input(cmd, source="voice", request_id=req_id)
dur_ms = (time.perf_counter() - start_t) * 1000.0

setattr(AIResponseManager, 'generate_response_streaming', original_gen)

print(f"\n[DUPLICATE AUDIT RESULT]", flush=True)
print(f"Command: '{cmd}'", flush=True)
print(f"Total Ollama API Requests Triggered: {len(request_tracker)}", flush=True)
for idx, r in enumerate(request_tracker, 1):
    print(f"  Request #{idx}: model={r['model']} keep_alive={r['keep_alive']} num_ctx={r['options'].get('num_ctx')} num_predict={r['options'].get('num_predict')} think={r['think']}", flush=True)
print(f"Total Command Duration: {dur_ms:.1f} ms\n", flush=True)


# -------------------------------------------------------------------
# 2. MEASURE PROMPT SIZES & METADATA
# -------------------------------------------------------------------
print("--- TEST 2: PROMPT SIZE & METADATA MEASUREMENT ---", flush=True)
queries = [
    "hello jarvis",
    "are you lookin good",
    "how are you today",
    "Jarvis, explain Python in three sentences in simple Hinglish."
]

for q in queries:
    messages, intel, conv_mgr = _build_pipeline(q, "Boss", "boss")
    sys_prompt = messages[0]["content"]
    user_msg = messages[-1]["content"]
    hist_msgs = messages[1:-1]

    sys_chars = len(sys_prompt)
    hist_chars = sum(len(m.get("content", "")) for m in hist_msgs)
    user_chars = len(user_msg)
    total_chars = sum(len(m.get("content", "")) for m in messages)
    est_tokens = total_chars // 4

    print(f"Query: '{q}'", flush=True)
    print(f"  system_prompt_chars:            {sys_chars}", flush=True)
    print(f"  conversation_history_messages:  {len(hist_msgs)}", flush=True)
    print(f"  conversation_history_chars:     {hist_chars}", flush=True)
    print(f"  user_input_chars:               {user_chars}", flush=True)
    print(f"  prompt_chars (total):           {total_chars}", flush=True)
    print(f"  estimated_prompt_tokens:        ~{est_tokens}\n", flush=True)


# -------------------------------------------------------------------
# 3. CONTROLLED BENCHMARK: 3 CONSECUTIVE TURNS + IDLE TURN
# -------------------------------------------------------------------
print("--- TEST 3: CONTROLLED BENCHMARK ('Jarvis, what is Python?') ---", flush=True)
ctrl_query = "Jarvis, what is Python?"
ctrl_results = []

for run_num in range(1, 4):
    sys_before = get_system_telemetry()
    ps_before = get_ollama_ps()

    req_id = f"ctrl_run_{run_num}"
    
    first_token_time = [None]
    first_sentence_time = [None]
    chunks = []

    def mock_cb(chunk):
        now = time.perf_counter()
        if first_sentence_time[0] is None:
            first_sentence_time[0] = now
        chunks.append(chunk)

    pipe_start = time.perf_counter()

    resp = ask_ollama_streaming(
        user_input=ctrl_query,
        speaker_name="Boss",
        relation="boss",
        speak_callback=mock_cb,
        speech_coordinator=speech_coordinator,
        request_id=req_id
    )

    pipe_end = time.perf_counter()
    tot_ms = (pipe_end - pipe_start) * 1000.0
    first_tok_ms = ((first_sentence_time[0] - pipe_start) * 1000.0) if first_sentence_time[0] else tot_ms

    sys_after = get_system_telemetry()
    ps_after = get_ollama_ps()

    model_loaded = len(ps_after) > 0 and ps_after[0].get("name") == MODEL_NAME

    rec = {
        "run": run_num,
        "first_token_ms": first_tok_ms,
        "first_sentence_ms": first_tok_ms,
        "total_ms": tot_ms,
        "model_warm": model_loaded,
        "available_ram_mb": sys_after["available_ram_mb"],
        "ollama_cpu": sys_after["ollama_cpu_percent"]
    }
    ctrl_results.append(rec)

    print(f"Run {run_num}:", flush=True)
    print(f"  First Token Latency:          {first_tok_ms:.1f} ms ({first_tok_ms/1000.0:.2f} s)", flush=True)
    print(f"  First Sentence Complete:      {first_tok_ms:.1f} ms ({first_tok_ms/1000.0:.2f} s)", flush=True)
    print(f"  Total Response Time:          {tot_ms:.1f} ms ({tot_ms/1000.0:.2f} s)", flush=True)
    print(f"  Model Loaded Warm:            {model_loaded}", flush=True)
    print(f"  System RAM Available:         {sys_after['available_ram_mb']:.1f} MB (Used: {sys_after['ram_percent']}%)", flush=True)
    print(f"  Ollama Process CPU:           {sys_after['ollama_cpu_percent']}%\n", flush=True)

    time.sleep(1.0)

# Idle test after 5 seconds
print("Waiting 5 seconds for post-idle retention test...", flush=True)
time.sleep(5.0)

idle_start = time.perf_counter()
first_sent_idle = [None]
def mock_cb_idle(chunk):
    if first_sent_idle[0] is None:
        first_sent_idle[0] = time.perf_counter()

resp_idle = ask_ollama_streaming(
    user_input=ctrl_query,
    speaker_name="Boss",
    relation="boss",
    speak_callback=mock_cb_idle,
    speech_coordinator=speech_coordinator,
    request_id="ctrl_run_4_idle"
)
idle_end = time.perf_counter()
idle_tot_ms = (idle_end - idle_start) * 1000.0
idle_first_tok_ms = ((first_sent_idle[0] - idle_start) * 1000.0) if first_sent_idle[0] else idle_tot_ms

print(f"Run 4 (After 5s Idle):", flush=True)
print(f"  First Token Latency:          {idle_first_tok_ms:.1f} ms ({idle_first_tok_ms/1000.0:.2f} s)", flush=True)
print(f"  Total Response Time:          {idle_tot_ms:.1f} ms ({idle_tot_ms/1000.0:.2f} s)\n", flush=True)

print("=======================================================", flush=True)
print("FINAL SUMMARY TABLE", flush=True)
print("=======================================================", flush=True)
for r in ctrl_results:
    print(f"Run {r['run']}: First Token = {r['first_token_ms']:.1f} ms | Total = {r['total_ms']:.1f} ms | Model Warm = {r['model_warm']}", flush=True)
print(f"Run 4 (After 5s Idle): First Token = {idle_first_tok_ms:.1f} ms | Total = {idle_tot_ms:.1f} ms", flush=True)
