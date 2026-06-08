import speech_recognition as sr
import webbrowser
import pyttsx3

# Initialize
r = sr.Recognizer()
engine = pyttsx3.init()

# Text to Speech
def speak(text):
    global engine
    engine.stop()
    engine.say(text)
    engine.runAndWait()

# Process Commands
def processCommand(command):
    command = command.lower()

    if "open google" in command:
        speak("Opening Google")
        webbrowser.open("https://google.com")

    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    elif "open spotify" in command:
        speak("Opening Spotify")
        webbrowser.open("https://spotify.com")

    else:
        speak("Command not recognized")


# Main Program
if __name__ == "__main__":
    speak("Initializing Jarvis")

    # Calibrate microphone once at startup
    print("Calibrating microphone for ambient noise...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
    print("Calibration complete. Listening for wake word...")

    while True:
        try:
            # Listen for wake word
            with sr.Microphone() as source:
                print("Listening for wake word...")
                audio = r.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=3
                )

            word = r.recognize_google(audio, language="en-IN")
            print("Wake Word:", word)

            # Check wake word
            if "jarvis" in word.lower():

                print("Jarvis detected")
                speak("Yes boss")

                # Listen for command
                with sr.Microphone() as source:
                    print("Listening for command...")

                    r.adjust_for_ambient_noise(source, duration=0.5)

                    audio = r.listen(
                        source,
                        timeout=8,
                        phrase_time_limit=8
                    )

                command = r.recognize_google(
                    audio,
                    language="en-IN"
                )

                print("Command:", command)

                processCommand(command)

        except sr.UnknownValueError:
            print("Could not understand audio")

        except sr.WaitTimeoutError:
            print("No speech detected")

        except Exception as e:
            print("Error:", repr(e))