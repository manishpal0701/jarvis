import os
import threading
from video_editing.video_intent_router import VideoIntentRouter, classify_video_intent
from video_editing.video_session_manager import VideoEditingSessionManager

_editor_agent = None

def get_editor_agent():
    global _editor_agent
    if _editor_agent is None:
        from video_editing.agents.editor_agent import VideoEditorAgent
        _editor_agent = VideoEditorAgent()
    return _editor_agent

def handle_video_command(command, speak_func):
    """
    Routes video editing commands to the VideoEditorAgent.
    """
    agent = get_editor_agent()
    threading.Thread(target=agent.process, args=(command, speak_func)).start()
