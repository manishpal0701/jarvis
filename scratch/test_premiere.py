import win32com.client
import sys

def test_connection():
    print("Attempting to connect to Premiere Pro...")
    try:
        # Try different ProgIDs
        prog_ids = ["Premiere Pro.Application", "Premiere Pro.App", "PremierePro.Application"]
        for prog_id in prog_ids:
            try:
                print(f"Trying {prog_id}...")
                app = win32com.client.Dispatch(prog_id)
                print(f"Successfully connected using {prog_id}!")
                print(f"App object: {app}")
                # Try to evaluate a simple script
                result = app.EvaluateScript("app.version")
                print(f"Premiere version: {result}")
                return
            except Exception as e:
                print(f"Failed with {prog_id}: {e}")
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    test_connection()
