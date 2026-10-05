import time
import os
import sys
from config import MODEL_NAME
from ai.model_router import ModelRouter
from ai.ask_ollama import ask_ollama
from conversation.command_router import CommandRouter
from conversation.conversation_manager import ConversationManager

def run_tests():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("JARVIS REAL CONVERSATION MIGRATION TEST SUITE (qwen3:8b)")
    print("=" * 70)

    router = ModelRouter.get_instance()
    cmd_router = CommandRouter()
    conv_mgr = ConversationManager()
    conv_mgr.clear_history()

    test_queries = [
        ("TEST 1", "mujhe ek Maggi ki recipe do"),
        ("TEST 2", "accha agar usme cheese add karu to?"),
        ("TEST 3", "Jarvis, mera naam kya hai?"),
        ("TEST 4", "Python aur Flutter me difference kya hai?"),
        ("TEST 5", "what were we talking about?"),
        ("TEST 6", "Jarvis, ek modern restaurant website bana do")
    ]

    results = []

    for test_id, query in test_queries:
        print(f"\n[{test_id}]: User Prompt: '{query}'")
        t0 = time.time()

        # Check intent / route
        if cmd_router.is_coding_task(query):
            pipeline_type = "WEBSITE_BUILDER_PIPELINE"
            selected_model = f"phi4-mini (routing) -> qwen3:8b (research) -> qwen3:4b-instruct (coding)"
            context_maintained = "N/A (Website Build Task)"
            response_text = "[Triggered Website Builder Code Assistant Pipeline]"
        else:
            pipeline_type = "GENERAL_CONVERSATION_PIPELINE"
            selected_model = router.get_model_for_task("general_conversation")
            response_text = ask_ollama(query, speaker_name="Manish", relation="owner")
            
            # Check context maintenance
            context = conv_mgr.get_history_context()
            context_maintained = "YES" if len(context) > 0 else "NO"

        latency = round(time.time() - t0, 2)

        print(f"  Selected Model:      {selected_model}")
        print(f"  Response Latency:    {latency}s")
        print(f"  Context Maintained:  {context_maintained}")
        print(f"  Pipeline Triggered:  {pipeline_type}")
        print(f"  Response:\n  {response_text.strip()}")

        results.append({
            "test_id": test_id,
            "query": query,
            "selected_model": selected_model,
            "response": response_text.strip(),
            "latency": latency,
            "context_maintained": context_maintained,
            "pipeline_type": pipeline_type
        })

    print("\n" + "=" * 70)
    print("MIGRATION TEST VERIFICATION SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"{r['test_id']} ({r['query']}):")
        print(f"  Model: {r['selected_model']} | Latency: {r['latency']}s | Pipeline: {r['pipeline_type']}")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
