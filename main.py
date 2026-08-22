import os
import sys
import warnings

# Suppress log noise
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
warnings.filterwarnings("ignore")

import speech
from conversation.conversation_engine import ConversationEngine

def main():
    print("==========================================")
    print("       JARVIS AI ASSISTANT STARTUP        ")
    print("==========================================")
    
    # 1. Initialize global speech engine
    speech.initialize()
    speech.speak("Initializing Jarvis")

    # 2. Instantiate main Conversation Engine orchestrator
    engine = ConversationEngine()

    # 3. Run continuous conversation loop
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nJarvis shutting down gracefully...")
    finally:
        speech.shutdown()

if __name__ == "__main__":
    main()