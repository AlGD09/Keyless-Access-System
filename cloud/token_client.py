#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /cloud/token_client.py

import os
import requests

BASE_URL = os.getenv("CLOUD_BASE_URL", "http://10.42.0.1:8080/api")

class CloudError(RuntimeError):
    pass

def fetch_token_by_numeric_id(device_numeric_id: int, timeout_s: float = 4.0) -> str:
    """
    GET /api/devices/token/{id}
    Erwartet entweder {"token":"<hex>"} oder Plain-Text "<hex>".
    Rückgabe: Hex-String (lower), ohne 0x.
    """
    url = f"{BASE_URL}/devices/token/{device_numeric_id}"
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=timeout_s)
        r.raise_for_status()
    except requests.RequestException as e:
        raise CloudError(f"Token GET failed for id={device_numeric_id}: {e}") from e

    ctype = (r.headers.get("Content-Type") or "").lower()
    token_hex = r.json().get("token") if "application/json" in ctype else r.text.strip()
    token_hex = (token_hex or "").strip().lower()
    if not token_hex or not _is_hex(token_hex):
        raise CloudError(f"Ungültiges Token-Format für id={device_numeric_id}: {token_hex!r}")
    return token_hex

def _is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return len(s) % 2 == 0
    except Exception:
        return False