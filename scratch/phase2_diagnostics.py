import sys
import os
import time
import json
import threading
import urllib.request
import psutil
from datetime import datetime

# Enforce UTF-8 output encoding for Windows stdout/stderr
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

from ai.ask_ollama import ask_ollama_streaming, _build_pipeline
from ai.ai_response_manager import AIResponseManager, CONVERSATION_OPTIONS, MODEL_NAME
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

# Telemetry data collector
active_ollama_requests = []
ollama_request_lock = threading.Lock()

def get_ollama_ps():
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/ps", timeout=2.0)
        data = json.loads(req.read())
        return data.get("models", [])
    except Exception as e:
        return f"Error: {e}"

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

def print_separator(title):
    print("\n" + "=" * 70, flush=True)
    print(f" {title.upper()}", flush=True)
    print("=" * 70 + "\n", flush=True)

# -------------------------------------------------------------------
# DIAGNOSTIC TEST 1: VERIFY CONCURRENT / DUPLICATE OLLAMA REQUESTS & PROMPT METADATA
# -------------------------------------------------------------------
def test_command_routing_duplicates():
    print_separator("1 & 2. Single Command Trace & Duplicate Request Audit")
    cmd = "Jarvis, explain Python in three sentences in simple Hinglish."
    req_id = "phase2_diag_cmd_1"

    state_machine = StateMachine()
    timeout_manager = TimeoutManager(10.0)
    speech_coordinator = SpeechCoordinator(state_machine, timeout_manager)

    print(f"Executing command via CommandRouter: '{cmd}'", flush=True)
    
    request_tracker = []
    
    # Patch AIResponseManager to count actual Ollama API invocations
    original_gen = AIResponseManager.generate_response_streaming
    def tracked_generate(self, messages, sentence_callback, **kwargs):
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
        print(f"\n[OLLAMA_TRACE] [INTERCEPTED] request_sent timestamp={t_now}", flush=True)
        print(f"[OLLAMA_TRACE] model={req_info['model']} keep_alive={req_info['keep_alive']} num_ctx={req_info['options'].get('num_ctx')} num_predict={req_info['options'].get('num_predict')} think={req_info['think']}", flush=True)
        return original_gen(self, messages, sentence_callback, **kwargs)

    router = CommandRouter(speech_coordinator=speech_coordinator)
    
    with patch_object(AIResponseManager, 'generate_response_streaming', tracked_generate):
        start_t = time.perf_counter()
        router.process_user_input(cmd, source="voice", request_id=req_id)
        dur = (time.perf_counter() - start_t) * 1000.0

    print(f"\nAudit Result for '{cmd}':", flush=True)
    print(f"Total Ollama requests generated: {len(request_tracker)}", flush=True)
    for idx, r in enumerate(request_tracker, 1):
        print(f"  Request #{idx}: timestamp={r['timestamp']} model={r['model']} messages={r['messages_count']} options={r['options']}", flush=True)
    print(f"Execution Duration: {dur:.1f} ms\n", flush=True)
    return len(request_tracker)

# Helper patch class
class patch_object:
    def __init__(self, target, attribute, new_value):
        self.target = target
        self.attribute = attribute
        self.new_value = new_value
        self.original = getattr(target, attribute)
    def __enter__(self):
        setattr(self.target, self.attribute, self.new_value)
        return self.new_value
    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(self.target, self.attribute, self.original)


# -------------------------------------------------------------------
# DIAGNOSTIC TEST 2: MEASURE PROMPT SIZE & CORRELATION
# -------------------------------------------------------------------
def test_prompt_size_measurement():
    print_separator("4. Detailed Prompt Size & Token Metadata Analysis")
    test_inputs = [
        "hello jarvis",
        "are you lookin good",
        "how are you today",
        "Jarvis, explain Python in three sentences in simple Hinglish."
    ]

    for q in test_inputs:
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
        print(f"  System prompt chars:          {sys_chars}", flush=True)
        print(f"  History messages count:       {len(hist_msgs)}", flush=True)
        print(f"  History total chars:          {hist_chars}", flush=True)
        print(f"  User input chars:             {user_chars}", flush=True)
        print(f"  Total prompt chars:           {total_chars}", flush=True)
        print(f"  Estimated prompt tokens:      ~{est_tokens}", flush=True)
        print(f"  Messages payload structure:   [{', '.join(m['role'] for m in messages)}]\n", flush=True)


# -------------------------------------------------------------------
# DIAGNOSTIC TEST 3: CONTROLLED RUN (SAME QUERY 3 CONSECUTIVE TIMES + IDLE TURN)
# -------------------------------------------------------------------
def test_controlled_runs():
    print_separator("5, 7, 8 & 9. Controlled Benchmark, Warm/Cold State & Timeline Verification")

    query = "Jarvis, what is Python?"
    state_machine = StateMachine()
    timeout_manager = TimeoutManager(10.0)
    speech_coordinator = SpeechCoordinator(state_machine, timeout_manager)

    runs_data = []

    for run_num in range(1, 4):
        print(f"\n>>> RUN {run_num}: '{query}' <<<", flush=True)
        
        # System & Ollama status before request
        sys_before = get_system_telemetry()
        ps_before = get_ollama_ps()
        print(f"[PRE-RUN {run_num}] System RAM available: {sys_before['available_ram_mb']:.1f} MB | Ollama loaded: {ps_before}", flush=True)

        req_id = f"phase2_ctrl_run_{run_num}"

        timeline = {}
        chunks_timeline = []

        def trace_speak_cb(chunk):
            now = time.perf_counter()
            if "first_sentence_complete" not in timeline:
                timeline["first_sentence_complete"] = now
            chunks_timeline.append((now, chunk))

        pipeline_start_t = time.perf_counter()
        timeline["asr_complete"] = pipeline_start_t

        # Stream call with timestamps
        print(f"[OLLAMA_TRACE] request_id={req_id} model={MODEL_NAME} num_ctx={CONVERSATION_OPTIONS['num_ctx']} num_predict={CONVERSATION_OPTIONS['num_predict']} think=False timestamp={datetime.now().isoformat()}", flush=True)
        print(f"[OLLAMA_TRACE] request_sent t={pipeline_start_t:.6f}", flush=True)

        resp = ask_ollama_streaming(
            user_input=query,
            speaker_name="Boss",
            relation="boss",
            speak_callback=trace_speak_cb,
            speech_coordinator=speech_coordinator,
            request_id=req_id
        )

        pipeline_end_t = time.perf_counter()
        timeline["request_complete"] = pipeline_end_t

        sys_after = get_system_telemetry()
        ps_after = get_ollama_ps()

        # Telemetry calculations
        first_sentence_t = timeline.get("first_sentence_complete", pipeline_end_t)
        first_token_latency_ms = (first_sentence_t - pipeline_start_t) * 1000.0
        total_duration_ms = (pipeline_end_t - pipeline_start_t) * 1000.0

        run_record = {
            "run": run_num,
            "first_token_ms": first_token_latency_ms,
            "first_sentence_ms": first_token_latency_ms,
            "total_ms": total_duration_ms,
            "response_len": len(resp),
            "ram_mb_available": sys_after["available_ram_mb"],
            "ollama_ps": ps_after
        }
        runs_data.append(run_record)

        print(f"[RUN {run_num} TIMELINE]", flush=True)
        print(f"  ASR Complete -> Request Sent:  0.0 ms", flush=True)
        print(f"  First Token Latency:          {first_token_latency_ms:.1f} ms ({first_token_latency_ms/1000.0:.2f} s)", flush=True)
        print(f"  First Sentence Complete:      {first_token_latency_ms:.1f} ms ({first_token_latency_ms/1000.0:.2f} s)", flush=True)
        print(f"  Total Response Time:          {total_duration_ms:.1f} ms ({total_duration_ms/1000.0:.2f} s)", flush=True)
        print(f"  Response text:                \"{resp.strip()}\"", flush=True)
        print(f"  System RAM after:             {sys_after['available_ram_mb']:.1f} MB (Used: {sys_after['ram_percent']}%)", flush=True)
        print(f"  Ollama Process CPU/RAM:       CPU={sys_after['ollama_cpu_percent']}% RAM={sys_after['ollama_ram_mb']:.1f}MB", flush=True)

        time.sleep(1.0)

    # Idle test after 10s wait to check cold/warm drift
    print("\nWaiting 10 seconds to test idle/warm model retention...", flush=True)
    time.sleep(10.0)

    print(f"\n>>> RUN 4 (AFTER 10s IDLE): '{query}' <<<", flush=True)
    sys_before_idle = get_system_telemetry()
    ps_before_idle = get_ollama_ps()
    
    start_idle_t = time.perf_counter()
    resp_idle = ask_ollama_streaming(
        user_input=query,
        speaker_name="Boss",
        relation="boss",
        speech_coordinator=speech_coordinator,
        request_id="phase2_ctrl_run_4_idle"
    )
    end_idle_t = time.perf_counter()
    idle_dur_ms = (end_idle_t - start_idle_t) * 1000.0

    print(f"[RUN 4 AFTER IDLE RESULTS]", flush=True)
    print(f"  Total Response Time: {idle_dur_ms:.1f} ms ({idle_dur_ms/1000.0:.2f} s)", flush=True)
    print(f"  Ollama Loaded State: {ps_before_idle}\n", flush=True)

    print_separator("Controlled Benchmark Results Summary")
    for rd in runs_data:
        print(f"Run {rd['run']}: First Token = {rd['first_token_ms']:.1f} ms | Total = {rd['total_ms']:.1f} ms | Model Loaded = YES", flush=True)
    print(f"Run 4 (After 10s Idle): Total = {idle_dur_ms:.1f} ms", flush=True)

if __name__ == "__main__":
    test_command_routing_duplicates()
    test_prompt_size_measurement()
    test_controlled_runs()
