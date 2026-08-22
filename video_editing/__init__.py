
import os
import threading
from video_editing.agents.editor_agent import VideoEditorAgent

# Initialize the agent
editor_agent = VideoEditorAgent()

def handle_video_command(command, speak_func):
    """
    Routes video editing commands to the VideoEditorAgent.
    """
    threading.Thread(target=editor_agent.process, args=(command, speak_func)).start()
