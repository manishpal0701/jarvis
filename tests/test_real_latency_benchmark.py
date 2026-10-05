import time
import io
import sys
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager
from speech.queue_manager import QueueManager

def run_benchmark():
    sm = StateMachine()
    tm = TimeoutManager(10.0)
    coordinator = SpeechCoordinator(sm, tm)
    router = CommandRouter(speech_coordinator=coordinator)

    print("Running Real Backend Response Latency Benchmark...", flush=True)

    queries = [
        "Hello Jarvis",
        "Mera mood bahut kharab hai kya"
    ]

    for q in queries:
        start_t = time.perf_counter()
        req_id = f"req_bench_{int(time.time()*1000)}"
        print(f"\n--- Testing Query: '{q}' ({req_id}) ---", flush=True)
        try:
            router.route_command(q, source="voice", sync_execution=True, request_id=req_id)
        except Exception as e:
            print(f"Error during benchmark query: {e}", flush=True)
        dur = time.perf_counter() - start_t
        print(f"--- Completed Query in {dur:.2f} seconds ---\n", flush=True)

if __name__ == "__main__":
    run_benchmark()
