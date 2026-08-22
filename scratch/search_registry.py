import winreg

def search_registry():
    print("Searching registry for Premiere ProgIDs...")
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "")
        i = 0
        while True:
            try:
                name = winreg.EnumKey(key, i)
                if "premiere" in name.lower():
                    print(name)
                i += 1
            except OSError:
                break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_registry()
