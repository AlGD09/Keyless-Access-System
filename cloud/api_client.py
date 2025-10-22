#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from urllib.parse import quote

def get_target_manufacturer_id(rcu_id="A116G61", base_url="http://10.42.0.1:8080", timeout_s=4):
    """
    Fragt die Cloud nach dem zugewiesenen Smartphone und gibt die deviceId (hex) zurück.
    - rcu_id wird getrimmt & gequotet (verhindert Whitespaces in der URL)
    - Spezifikation sagt POST; wenn der Server 405 liefert, fällt es auf GET zurück.
    """
    rcu_id = str(rcu_id).strip()
    url = f"{base_url}/api/rcu/{quote(rcu_id)}/smartphones"
    headers = {"Accept": "application/json"}

    try:
        # Erst POST (gemäß ursprünglicher Anforderung) …
        resp = requests.post(url, headers=headers, timeout=timeout_s)
        # … wenn nicht erlaubt, auf GET ausweichen
        if resp.status_code == 405:
            resp = requests.get(url, headers=headers, timeout=timeout_s)

        resp.raise_for_status()
        data = resp.json() or {}
        dev_id = data.get("deviceId")
        if dev_id:
            return str(dev_id).strip().lower()  # in lowercase, ohne Whitespaces
        return None
    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei Anfrage: {e}")
        return None
