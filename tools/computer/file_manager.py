import os

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None

def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
    except Exception:
        pass

def create_file(path):
    try:
        open(path, "w", encoding="utf-8", errors="ignore").close()
    except Exception:
        pass
