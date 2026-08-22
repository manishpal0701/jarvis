from memory.memory_manager import MemoryManager

def load_memory() -> dict:
    """
    Backwards compatible load_memory function.
    Delegates to MemoryManager to return a dictionary view of memories.
    """
    mgr = MemoryManager()
    user_mems = mgr.retrieve_user_memory()
    result = {}
    for item in user_mems:
        meta = item.get("metadata", {})
        if "preference_key" in meta and "preference_value" in meta:
            result[meta["preference_key"]] = meta["preference_value"]
        else:
            result[item["id"]] = item.get("content")
    return result

def save_memory(memory: dict | str) -> bool:
    """
    Backwards compatible save_memory function.
    Delegates to MemoryManager to store user memories safely.
    """
    mgr = MemoryManager()
    if isinstance(memory, dict):
        for k, v in memory.items():
            mgr.store_user_preference(str(k), str(v))
        return True
    elif isinstance(memory, str):
        mem_id = mgr.store(content=memory, memory_type="user", source="legacy_save_memory")
        return mem_id is not None
    return False
