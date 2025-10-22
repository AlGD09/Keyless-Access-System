#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auth/challenge_response.py – Logik für Challenge-Response-Authentifizierung
"""

import hmac
import hashlib
import os
from typing import Optional


# Gemeinsamer Schlüssel (Testversion)
# SHARED_KEY = b"this_is_test_key_32bytes5555"
# SHARED_KEY = bytes.fromhex("296695f03a22452ca59ecd0eeb5e805c")

SHARED_KEY: Optional[bytes] = None

# Optionaler Fallback für lokale Tests (z. B. export SHARED_KEY_HEX=... )
_env_hex = os.getenv("SHARED_KEY_HEX")
if _env_hex:
    try:
        SHARED_KEY = bytes.fromhex(_env_hex.strip())
    except Exception:
        SHARED_KEY = None

def set_shared_key_hex(token_hex: str) -> None:
    """Setzt den Shared Key aus einem Hex-String."""
    global SHARED_KEY
    SHARED_KEY = bytes.fromhex(token_hex)

def set_shared_key(key_bytes: bytes) -> None:
    """Setzt den Shared Key direkt als Bytes."""
    global SHARED_KEY
    SHARED_KEY = key_bytes

def require_key() -> bytes:
    """Liefert den aktuell gesetzten Key oder wirft einen klaren Fehler."""
    if SHARED_KEY is None:
        raise RuntimeError("Shared key not set. Fetch token from cloud first.")
    return SHARED_KEY

def generate_expected_response(challenge: bytes) -> bytes:
    """
    Berechnet den erwarteten Response als HMAC-SHA256 über die Challenge.
    Nutzt den zur Laufzeit gesetzten Shared Key.
    """
    key = require_key()
    return hmac.new(key, challenge, hashlib.sha256).digest()

def verify_response(challenge: bytes, response: bytes) -> bool:
    """
    Prüft, ob die empfangene Response dem erwarteten Wert entspricht.
    """
    expected = generate_expected_response(challenge)
    return hmac.compare_digest(response, expected)