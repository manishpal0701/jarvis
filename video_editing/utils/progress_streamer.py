
import time
import sys

class ProgressStreamer:
    def __init__(self, speak_f=None):
        self.speak_f = speak_f

    def update_status(self, step, message, progress=None):
        """Minimal status update."""
        pass

    def explain(self, decision):
        """Displays and speaks the AI's reasoning clearly."""
        # Map certain steps to the user's requested professional strings
        if "Step 1" in decision: print("\nScanning videos...\n")
        elif "Step 2" in decision: print("Analyzing clips...\n")
        elif "Step 5" in decision: print("Creating timeline...\n")
        elif "Step 6" in decision: print("Rendering...\n")
        elif "Transferring" in decision: print("Export completed.\n")
        
        if self.speak_f:
            self.speak_f(decision)
            
    def stream_step(self, step_name, duration=1.5):
        """Silently simulates progress."""
        time.sleep(duration)
