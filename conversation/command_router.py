import re
import webbrowser

class CommandRouter:
    """
    Unified Command Router for Jarvis.
    Maps user input to system tools, feature subpackages, or Ollama conversational AI.
    """

    def __init__(self, speech_coordinator=None):
        self.speech_coordinator = speech_coordinator
        self._code_assistant = None
        self._stock_analyzer = None
        self._face_recognizer = None

    def _speak(self, text: str):
        if self.speech_coordinator:
            self.speech_coordinator.speak(text)
        else:
            print(f"Jarvis: {text}")

    def get_code_assistant(self):
        if self._code_assistant is None:
            from tools.coding.code_assistant import CodeAssistant
            self._code_assistant = CodeAssistant()
        return self._code_assistant

    def get_stock_analyzer(self):
        if self._stock_analyzer is None:
            try:
                from finance.stock_analyzer import StockAnalyzer
                self._stock_analyzer = StockAnalyzer()
            except Exception as e:
                print(f"StockAnalyzer import error: {e}")
        return self._stock_analyzer

    def get_face_recognizer(self):
        if self._face_recognizer is None:
            try:
                from vision.face_recognize import FaceRecognizer
                self._face_recognizer = FaceRecognizer()
            except Exception as e:
                print(f"FaceRecognizer import error: {e}")
        return self._face_recognizer

    def is_coding_task(self, cmd: str) -> bool:
        cmd_lower = cmd.lower()
        coding_keywords = [
            "bana do", "banaa do", "banao", "create website", "build website", "make website",
            "website", "script", "program", "app", "code", "python script", "javascript", "html", "css"
        ]
        return any(kw in cmd_lower for kw in coding_keywords)

    def route_command(self, query: str):
        """Processes and routes user commands."""
        if not query or query.strip() == "" or query == "None":
            return

        command = query.strip()
        command_lower = command.lower()
        print(f"Processing command:\n{command}\n")

        # 1. System / Web Commands
        if "open google" in command_lower:
            self._speak("Opening Google")
            webbrowser.open("https://google.com")
            return

        if "open youtube" in command_lower:
            self._speak("Opening YouTube")
            webbrowser.open("https://youtube.com")
            return

        if "open spotify" in command_lower:
            self._speak("Opening Spotify")
            webbrowser.open("https://spotify.com")
            return

        # 2. Stock Analyzer
        if any(term in command_lower for term in ["stock price", "stock analysis", "share price"]):
            analyzer = self.get_stock_analyzer()
            if analyzer:
                res = analyzer.analyze_query(command)
                self._speak(res)
                return

        # 3. Face Recognition
        if any(term in command_lower for term in ["who am i", "recognize me", "face recognize", "recognize face"]):
            recognizer = self.get_face_recognizer()
            if recognizer:
                res = recognizer.recognize_current_user()
                self._speak(res)
                return

        # 4. Code Assistant & Website Builder
        if self.is_coding_task(command_lower):
            assistant = self.get_code_assistant()
            if assistant:
                self._speak("Right away Boss, working on the coding task.")
                code, path = assistant.generate_code(command)
                self._speak(f"Coding task finished, saved to {path}")
                return

        # 5. Fallback to Ollama Conversational Pipeline (handles general Q&A e.g. "what is Python")
        try:
            from ai.ask_ollama import ask_ollama_streaming
            def speak_cb(chunk):
                self._speak(chunk)
            ask_ollama_streaming(command, speaker_name="Boss", relation="boss", speak_callback=speak_cb)
        except Exception as e:
            print(f"[CommandRouter Ollama Fallback Error]: {e}")
            self._speak("I understood your query, but could not connect to Ollama.")
