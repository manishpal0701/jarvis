import ast
import os

files = [
    "ask_ollama.py",
    "chat_responses.py",
    "config.py",
    "face_recognize.py",
    "main.py",
    "memory.py",
    "monitor.py",
    "music_libary.py",
    "open_app.py"
]

for file in files:
    try:
        with open(file, "r") as f:
            ast.parse(f.read())
        print(f"{file}: Syntax OK")
    except Exception as e:
        print(f"{file}: Syntax Error - {e}")
