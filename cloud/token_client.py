#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /cloud/token_client.py

import os
import requests
from config import CLOUD_URL


class CloudError(RuntimeError):
    pass


def fetch_token_by_numeric_id(device_numeric_id: int, timeout_s: float = 4.0) -> str:
    """
    GET /api/devices/token/{id}
    Erwartet entweder {"token":"<hex>"} oder {"auth_token":"<hex>"} oder Plain-Text "<hex>".
    Rückgabe: Hex-String (lower), ohne 0x.
    """
    url = f"{CLOUD_URL}/api/devices/token/{device_numeric_id}"
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout_s)
        r.raise_for_status()
    except requests.RequestException as e:
        raise CloudError(f"Token GET failed for id={device_numeric_id}: {e}") from e

    token_raw = ""
    body = (r.text or "").strip()

    # --- JSON lesen, falls möglich ---
    try:
        js = r.json()
        if isinstance(js, dict):
            if "token" in js:
                token_raw = str(js["token"]).strip()
            elif "auth_token" in js:                
                token_raw = str(js["auth_token"]).strip()
    except Exception:
        pass

    # --- Falls kein JSON erkannt, Plain-Text verwenden ---
    if not token_raw and body:
        token_raw = body

    token_raw = token_raw.strip().lower()
    if not token_raw or not _is_hex(token_raw):
        raise CloudError(f"Ungültiges Token-Format für id={device_numeric_id}: {token_raw!r}")

    return token_raw


def _is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return len(s) % 2 == 0
    except Exception:
        return False
