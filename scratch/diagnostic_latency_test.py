import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import ollama

def run_diagnostic():
    print("==================================================")
    print("JARVIS LATENCY ROOT-CAUSE DIAGNOSTIC BENCHMARK")
    print("==================================================")

    prompt_test_a = "What is Python? Answer in one sentence."
    prompt_test_b = "Explain Python in 3 sentences. Answer naturally in simple Hinglish."

    # ---------------------------------------------------------
    # TEST A: Direct Ollama Test (Short)
    # ---------------------------------------------------------
    print("\n--- TEST A: Direct Ollama (Short Prompt) ---")
    t0 = time.perf_counter()
    client = ollama.Client()
    res_a = client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt_test_a}],
        options={"num_ctx": 512, "num_predict": 80, "temperature": 0.7, "top_p": 0.9},
        think=False,
        keep_alive=-1
    )
    t1 = time.perf_counter()
    dur_a = t1 - t0
    eval_count_a = res_a.get("eval_count", 0)
    prompt_tokens_a = res_a.get("prompt_eval_count", 0)
    eval_dur_a = (res_a.get("eval_duration", 0) or 0) / 1e9
    prompt_eval_dur_a = (res_a.get("prompt_eval_duration", 0) or 0) / 1e9
    print(f"Direct Ollama Test A Duration: {dur_a:.3f}s")
    print(f"  Prompt tokens: {prompt_tokens_a}, eval_dur: {prompt_eval_dur_a:.3f}s")
    print(f"  Output tokens: {eval_count_a}, eval_dur: {eval_dur_a:.3f}s")
    print(f"  Content: {res_a['message']['content'].encode('ascii', 'ignore').decode('ascii')}")

    # ---------------------------------------------------------
    # TEST B: Direct Ollama Test (Hinglish Prompt)
    # ---------------------------------------------------------
    print("\n--- TEST B: Direct Ollama (Hinglish Prompt) ---")
    t0 = time.perf_counter()
    res_b = client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt_test_b}],
        options={"num_ctx": 512, "num_predict": 80, "temperature": 0.7, "top_p": 0.9},
        think=False,
        keep_alive=-1
    )
    t1 = time.perf_counter()
    dur_b = t1 - t0
    eval_count_b = res_b.get("eval_count", 0)
    prompt_tokens_b = res_b.get("prompt_eval_count", 0)
    eval_dur_b = (res_b.get("eval_duration", 0) or 0) / 1e9
    prompt_eval_dur_b = (res_b.get("prompt_eval_duration", 0) or 0) / 1e9
    print(f"Direct Ollama Test B Duration: {dur_b:.3f}s")
    print(f"  Prompt tokens: {prompt_tokens_b}, eval_dur: {prompt_eval_dur_b:.3f}s")
    print(f"  Output tokens: {eval_count_b}, eval_dur: {eval_dur_b:.3f}s")
    print(f"  Content: {res_b['message']['content'].encode('ascii', 'ignore').decode('ascii')}")

    # ---------------------------------------------------------
    # TEST C: Direct Ollama Test with Full System Prompt
    # ---------------------------------------------------------
    print("\n--- TEST C: Direct Ollama (Full System Prompt + 512 Context) ---")
    from ai.ask_ollama import _build_system_prompt
    sys_prompt = _build_system_prompt("Boss", "boss", {}, "")
    full_messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt_test_b}
    ]
    t0 = time.perf_counter()
    res_c = client.chat(
        model="qwen3:8b",
        messages=full_messages,
        options={"num_ctx": 512, "num_predict": 80, "temperature": 0.7, "top_p": 0.9},
        think=False,
        keep_alive=-1
    )
    t1 = time.perf_counter()
    dur_c = t1 - t0
    eval_count_c = res_c.get("eval_count", 0)
    prompt_tokens_c = res_c.get("prompt_eval_count", 0)
    eval_dur_c = (res_c.get("eval_duration", 0) or 0) / 1e9
    prompt_eval_dur_c = (res_c.get("prompt_eval_duration", 0) or 0) / 1e9
    print(f"Direct Ollama Test C Duration: {dur_c:.3f}s")
    print(f"  Prompt chars: {sum(len(m['content']) for m in full_messages)}")
    print(f"  Prompt tokens: {prompt_tokens_c}, eval_dur: {prompt_eval_dur_c:.3f}s")
    print(f"  Output tokens: {eval_count_c}, eval_dur: {eval_dur_c:.3f}s")
    print(f"  Content: {res_c['message']['content'].encode('ascii', 'ignore').decode('ascii')}")

    # ---------------------------------------------------------
    # TEST D: Direct Ollama Streaming Test
    # ---------------------------------------------------------
    print("\n--- TEST D: Direct Ollama Streaming Test ---")
    t0 = time.perf_counter()
    stream = client.chat(
        model="qwen3:8b",
        messages=full_messages,
        options={"num_ctx": 512, "num_predict": 80, "temperature": 0.7, "top_p": 0.9},
        think=False,
        stream=True,
        keep_alive=-1
    )
    first_token_t = None
    chunks_count = 0
    full_str_d = []
    for chunk in stream:
        if first_token_t is None:
            first_token_t = time.perf_counter()
        chunks_count += 1
        txt = chunk.get("message", {}).get("content", "")
        full_str_d.append(txt)
    t1 = time.perf_counter()
    first_token_lat = first_token_t - t0 if first_token_t else (t1 - t0)
    total_lat_d = t1 - t0
    out_d_clean = "".join(full_str_d).encode('ascii', 'ignore').decode('ascii')
    print(f"Streaming Direct Test D Duration: {total_lat_d:.3f}s")
    print(f"  First token latency: {first_token_lat:.3f}s")
    print(f"  Total chunks received: {chunks_count}")
    print(f"  Content: {out_d_clean}")

    # ---------------------------------------------------------
    # TEST E: Full JARVIS Conversation Pipeline Telemetry
    # ---------------------------------------------------------
    print("\n--- TEST E: JARVIS Full Pipeline Step-by-Step Breakdown ---")
    base_clock = time.perf_counter()

    t_start = time.perf_counter()

    # 1. Command received
    t_cmd_rec = time.perf_counter()

    # 2. CommandRouter start
    t_router_start = time.perf_counter()
    from conversation.command_router import CommandRouter
    router = CommandRouter()

    # Priority checks simulation
    t_pri_check = time.perf_counter()

    # Priority 13: AgentOrchestrator
    t_orch_start = time.perf_counter()
    from agent.agent_orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator.get_instance()

    # Task Planner
    t_planner_start = time.perf_counter()
    task = orchestrator.planner.generate_plan(prompt_test_b)
    t_planner_end = time.perf_counter()

    # Context & Memory
    t_ctx_start = time.perf_counter()
    from conversation.conversation_manager import ConversationManager
    conv_mgr = ConversationManager.get_instance()
    conv_mgr.process_and_resolve_input(prompt_test_b)
    t_ctx_end = time.perf_counter()

    t_mem_start = time.perf_counter()
    from memory.memory_manager import MemoryManager
    mem_mgr = MemoryManager()
    mems = mem_mgr.retrieve_relevant(prompt_test_b, limit=3, min_score=0.5)
    t_mem_end = time.perf_counter()

    # Prompt building
    t_prompt_start = time.perf_counter()
    from ai.ask_ollama import _build_pipeline
    messages_built, intel, _ = _build_pipeline(prompt_test_b, "Boss", "boss")
    t_prompt_end = time.perf_counter()
    prompt_chars = sum(len(m["content"]) for m in messages_built)

    # Agent Handler Execution (_handle_conversation -> ask_ollama)
    t_handler_start = time.perf_counter()
    agent_res = orchestrator.orchestrate(prompt_test_b, source="voice")
    t_handler_end = time.perf_counter()

    t_end = time.perf_counter()

    res_clean = (agent_res.result[:100] if agent_res.result else "").encode('ascii', 'ignore').decode('ascii')
    print("\n==================================================")
    print("TELEMETRY RESULTS SUMMARY")
    print("==================================================")
    print(f"1.  COMMAND_RECEIVED_OFFSET = {(t_cmd_rec - t_start)*1000:.2f} ms")
    print(f"2.  ROUTER_START_OFFSET     = {(t_router_start - t_start)*1000:.2f} ms")
    print(f"3.  PLANNER_DURATION        = {(t_planner_end - t_planner_start)*1000:.2f} ms")
    print(f"4.  CONTEXT_RESOLVE_DUR     = {(t_ctx_end - t_ctx_start)*1000:.2f} ms")
    print(f"5.  MEMORY_RETRIEVAL_DUR    = {(t_mem_end - t_mem_start)*1000:.2f} ms")
    print(f"6.  PROMPT_BUILD_DUR        = {(t_prompt_end - t_prompt_start)*1000:.2f} ms")
    print(f"7.  FINAL_PROMPT_CHARS      = {prompt_chars} chars")
    print(f"8.  TOTAL_ORCHESTRATE_DUR   = {(t_handler_end - t_orch_start):.3f} seconds ({((t_handler_end - t_orch_start)*1000):.1f} ms)")
    print(f"9.  TOTAL_PIPELINE_DUR      = {(t_end - t_start):.3f} seconds")
    print(f"10. AGENT_RESULT_STATUS     = {agent_res.status}")
    print(f"11. AGENT_RESULT_TEXT       = {res_clean}")

if __name__ == "__main__":
    run_diagnostic()
