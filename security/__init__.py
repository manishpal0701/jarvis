"""
Security Package — Voice authentication, owner verification, and security permissions.
"""
from security.voice_security import verify_owner, OWNER_PASSWORD

__all__ = ["verify_owner", "OWNER_PASSWORD"]
