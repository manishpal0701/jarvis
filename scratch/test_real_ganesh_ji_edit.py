import sys
import os

from video_editing.video_session_manager import VideoEditingSessionManager

def main():
    media_folder = r"C:\Users\manis\Downloads\ganesh ji"
    cmd = f'ek cinematic video edit kar do "{media_folder}"'
    print(f"Executing: {cmd}")

    session = VideoEditingSessionManager.get_instance()
    session.reset_session()

    result = session.handle_command(cmd, sync_execution=True)
    print("\n" + "="*50)
    print("   REAL E2E EXECUTION RESULT   ")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()
