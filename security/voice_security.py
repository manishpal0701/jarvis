OWNER_PASSWORD = "Jarvis"  # Replace with your desired password

def verify_owner(password):
    return password.lower().strip() == OWNER_PASSWORD.lower()
