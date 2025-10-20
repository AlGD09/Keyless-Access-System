#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auth/challenge_response.py – Logik für Challenge-Response-Authentifizierung
"""

import hmac
import hashlib

# Gemeinsamer Schlüssel (Testversion)
# SHARED_KEY = b"this_is_test_key_32bytes5555"
SHARED_KEY = bytes.fromhex("296695f03a22452ca59ecd0eeb5e805c")

def generate_expected_response(challenge: bytes) -> bytes:
    """
    Berechnet den erwarteten Response als HMAC-SHA256 über die Challenge.
    """
    return hmac.new(SHARED_KEY, challenge, hashlib.sha256).digest()

def verify_response(challenge: bytes, response: bytes) -> bool:
    """
    Prüft, ob die empfangene Response dem erwarteten Wert entspricht.
    """
    expected = generate_expected_response(challenge)
    return hmac.compare_digest(response, expected)
