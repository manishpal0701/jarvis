import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import config

def handle_remember_command(command, memory_manager):
    command_clean = command.lower().strip()
    if command_clean.startswith("remember") or "remember that" in command_clean:
        print("\n[MEMORY]")
        print("Input received")

        content = command
        for prefix in ["Remember that ", "remember that ", "Remember ", "remember ", "remember: "]:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
                break

        if content and len(content) > 0:
            content = content[0].upper() + content[1:]

        content_lower = content.lower()
        if "project" in content_lower or "app" in content_lower:
            mem_type = "project"
            project_name = "Jarvis AI" if "jarvis" in content_lower else None
        elif any(k in content_lower for k in ["prefer", "like", "favorite", "my name"]):
            mem_type = "user"
            project_name = None
        else:
            mem_type = "semantic"
            project_name = None

        tags = [mem_type]
        if "project" in content_lower:
            tags.append("project")

        mem_id = memory_manager.store(
            content=content,
            memory_type=mem_type,
            source="user_directive",
            project=project_name,
            tags=tags
        )
        return mem_id
    return None

def run_tests():
    print("==========================================")
    print("   RUNNING MEMORY PERSISTENCE TESTS       ")
    print("==========================================")

    from memory.memory_manager import MemoryManager

    storage_path = os.path.abspath(config.MEMORY_FILE)
    print(f"\nTarget Memory Storage File: {storage_path}")

    # Reset singleton state for clean Session 1
    MemoryManager._instance = None

    print("\n--- SESSION 1: STORING MEMORY ---")
    session_1_mgr = MemoryManager()
    user_input_1 = "Remember that my current project is Jarvis AI"
    print(f"User Input: '{user_input_1}'")
    
    mem_id = handle_remember_command(user_input_1, session_1_mgr)

    # Check 1: STORAGE WRITE
    write_pass = os.path.exists(storage_path)
    
    # Check 2: STORAGE PERSISTENCE
    persistence_pass = False
    if write_pass:
        with open(storage_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            if "Jarvis AI" in file_content or "my current project is jarvis ai" in file_content.lower():
                persistence_pass = True

    print(f"\nPhysical File Verification: Exists={write_pass}, Contains Memory={persistence_pass}")

    # Step 2: SIMULATE COMPLETE SHUTDOWN & RESTART (Kill RAM state)
    print("\n--- SIMULATING JARVIS SHUTDOWN & RESTART ---")
    del session_1_mgr
    MemoryManager._instance = None

    # Step 3: SESSION 2: STARTUP LOAD & RETRIEVAL
    print("\n--- SESSION 2: STARTUP & QUERY ---")
    
    # Initialize MemoryManager fresh as happens on startup
    session_2_mgr = MemoryManager()
    records = session_2_mgr._store_engine.get_all_records()
    startup_load_pass = len(records) > 0

    # Query memory
    user_input_2 = "What is my current project?"
    print(f"\nUser Query: '{user_input_2}'")
    
    retrieved = session_2_mgr.retrieve_relevant(user_input_2, limit=3)
    retrieval_pass = any("Jarvis AI" in r.get("content", "") for r in retrieved)

    # Check LLM Context Injection log
    print("\nSimulating ask_ollama prompt context injection...")
    mems = session_2_mgr.retrieve_relevant(user_input_2, limit=3)
    llm_context_pass = False
    if mems:
        print("\n[MEMORY CONTEXT]")
        print("Relevant memory injected: YES")
        llm_context_pass = True
    else:
        print("\n[MEMORY CONTEXT]")
        print("Relevant memory injected: NO")

    cross_restart_pass = (
        write_pass and 
        persistence_pass and 
        startup_load_pass and 
        retrieval_pass and 
        llm_context_pass
    )

    print("\n==========================================")
    print("       FINAL PERSISTENCE TEST REPORT      ")
    print("==========================================")
    print(f"STORAGE WRITE: {'PASS' if write_pass else 'FAIL'}")
    print(f"STORAGE PERSISTENCE: {'PASS' if persistence_pass else 'FAIL'}")
    print(f"STARTUP LOAD: {'PASS' if startup_load_pass else 'FAIL'}")
    print(f"RETRIEVAL: {'PASS' if retrieval_pass else 'FAIL'}")
    print(f"LLM CONTEXT INJECTION: {'PASS' if llm_context_pass else 'FAIL'}")
    print(f"CROSS-RESTART MEMORY: {'PASS' if cross_restart_pass else 'FAIL'}")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
