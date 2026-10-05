import unittest
import time
from ai.ask_ollama import ask_ollama_streaming
from core.performance_profiler import PerformanceProfiler

class TestConversationLatency(unittest.TestCase):
    def test_streaming_response_latency(self):
        PerformanceProfiler.reset()
        start = time.perf_counter()
        first_chunk_time = None

        def callback(chunk):
            nonlocal first_chunk_time
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()

        response = ask_ollama_streaming("Hello Jarvis, how are you?", speaker_name="Boss", relation="boss", speak_callback=callback)
        total_duration = time.perf_counter() - start

        self.assertTrue(len(response) > 0)
        self.assertIsNotNone(first_chunk_time)

        first_chunk_latency = (first_chunk_time - start) * 1000.0
        print(f"\n[REAL_MEASURED_LATENCY] First Speakable Chunk: {first_chunk_latency:.2f} ms | Total: {total_duration*1000.0:.2f} ms", flush=True)

if __name__ == "__main__":
    unittest.main()
