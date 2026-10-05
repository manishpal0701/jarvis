import subprocess
import win32com.client
import time
import os

def test_launch_and_connect():
    premiere_path = r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"
    print("Launching Premiere Pro...")
    proc = subprocess.Popen([premiere_path])
    
    print("Waiting 15 seconds for Premiere Pro to start loading...")
    time.sleep(15)
    
    print("Attempting to connect via COM (PremierePro.Application)...")
    try:
        app = win32com.client.Dispatch("PremierePro.Application")
        print("Successfully connected to PremierePro.Application!")
        
        # Try to run a simple alert script
        print("Running DoScript alert...")
        app.DoScript("alert('Hello from Python COM!');")
        print("DoScript completed successfully!")
    except Exception as e:
        print(f"Failed to connect or run script: {e}")
        
    print("Terminating Premiere Pro process...")
    proc.terminate()

if __name__ == "__main__":
    test_launch_and_connect()
