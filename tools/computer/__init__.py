"""
Computer Tools — Application opening, file system operations, and local system control.
"""
from tools.computer.open_app import open_app
from tools.computer.file_manager import read_file, write_file, create_file
from tools.computer.music_libary import music

__all__ = [
    "open_app",
    "read_file",
    "write_file",
    "create_file",
    "music",
]
