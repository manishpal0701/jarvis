"""
scratch/manual_e2e_video_test.py
Manual E2E Test Script for Video Editing Agent.
Tests full pipeline on real video clips in C:\\Users\\manis\\Videos\\Bike edit.
"""

import os
import sys
import time

from video_editing.video_session_manager import VideoEditingSessionManager
from video_editing.analysis.media_analyzer import clear_media_cache


def run_e2e_test():
    bike_folder = r"C:\Users\manis\Videos\Bike edit"

    if os.path.isdir(bike_folder):
        target_folder = bike_folder
    else:
        print(f"[TEST_SETUP] '{bike_folder}' not found.")
        sys.exit(1)

    print("======================================================================")
    print(f"JARVIS VIDEO EDITING AGENT — REAL E2E PIPELINE TEST")
    print(f"Target Folder: {target_folder}")
    print("======================================================================\n")

    clear_media_cache()
    session = VideoEditingSessionManager.get_instance()
    session.reset_session()

    start_t = time.time()
    command = f"ek cinematic video edit karo '{target_folder}'"
    print(f"[INPUT_COMMAND] {command}\n")

    result = session.handle_command(command, sync_execution=True)
    total_sec = round(time.time() - start_t, 2)

    print("\n======================================================================")
    print(f"E2E EXECUTION COMPLETED IN {total_sec} SECONDS")
    print("======================================================================\n")
    print("RESULT SUMMARY:")
    print(result)
    print("\n======================================================================")


if __name__ == "__main__":
    run_e2e_test()
