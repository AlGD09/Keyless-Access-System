#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

def get_target_manufacturer_id(rcu_id="A116G61"):
    """Fragt die Cloud nach dem zugewiesenen Smartphone und gibt die deviceId zurück."""
    url = f"http://localhost:8080/api/rcu/{rcu_id}/smartphones"
    try:
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()
        return data.get("deviceId")
    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei Anfrage: {e}")
        return None
