import pyautogui
import pytesseract
import time

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\manis\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

def monitor_antigravity(speak):
    while True:
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)

        if "file modified" in text.lower():
            speak("Boss, the file has been modified. Please check it.")
            break
        time.sleep(10)  # Check every 10 seconds

def monitor_download(speak):
    while True:
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)

        if "download complete" in text.lower():
            speak("Boss, the download is complete. Please check it.")
            break
        time.sleep(5)  # Check every 5 seconds

def monitor_chatgpt(speak):
    while True:
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)

        if "new message" in text.lower():
            speak("Boss, you have a new message on ChatGPT. Please check it.")
            break
        time.sleep(5)  # Check every 5 seconds
