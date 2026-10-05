"""
tools/email/gmail_auth.py
Gmail OAuth 2.0 Authentication Manager for JARVIS.
Handles token caching, refresh, account identity, and graceful fallback.
"""

import os
import json
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("GmailAuthManager")

CREDENTIALS_PATH = os.path.join(os.path.expanduser("~"), ".jarvis", "gmail_credentials.json")
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".jarvis", "gmail_token.json")

class GmailAuthManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GmailAuthManager()
        return cls._instance

    def __init__(self):
        self._account_email: Optional[str] = None
        self._is_authenticated: bool = False
        self._load_token_status()

    def _load_token_status(self):
        if os.path.exists(TOKEN_PATH):
            try:
                with open(TOKEN_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._account_email = data.get("account_email", "user@gmail.com")
                    self._is_authenticated = True
            except Exception as e:
                logger.warning(f"Failed to parse token file: {e}")
                self._is_authenticated = False

    def is_authenticated(self) -> bool:
        return self._is_authenticated

    def get_account_email(self) -> str:
        return self._account_email or "Not Connected"

    def get_credentials(self) -> Tuple[bool, Optional[Any], str]:
        if not self._is_authenticated and not os.path.exists(TOKEN_PATH):
            return False, None, "Gmail OAuth token missing. Please run authentication flow."

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            creds = None
            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes=['https://mail.google.com/'])

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            if creds and creds.valid:
                self._is_authenticated = True
                return True, creds, "Gmail authenticated successfully."
            
            return False, None, "Invalid or expired Gmail credentials."
        except ImportError:
            if self._is_authenticated:
                return True, "MOCK_CREDENTIALS", "Mock credentials loaded for offline test mode."
            return False, None, "google-auth dependencies not installed and no valid token found."
        except Exception as e:
            logger.error(f"Gmail auth error: {e}")
            return False, None, f"Gmail auth error: {str(e)}"

    def set_mock_authenticated(self, account_email: str = "boss@gmail.com"):
        self._account_email = account_email
        self._is_authenticated = True

    def disconnect(self) -> bool:
        self._account_email = None
        self._is_authenticated = False
        if os.path.exists(TOKEN_PATH):
            try:
                os.remove(TOKEN_PATH)
            except Exception:
                pass
        return True
