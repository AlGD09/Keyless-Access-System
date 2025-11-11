# /cloud/api_client.py
import requests
from urllib.parse import quote
from config import CLOUD_URL
from config import RCU_ID

def get_assigned_smartphones(rcu_id=RCU_ID, base_url=CLOUD_URL, timeout_s=10):
    """
    Fragt die Cloud nach allen zugewiesenen Smartphones einer RCU.
    """
    
    rcu_id = str(rcu_id).strip()
    url = f"{base_url}/api/rcu/{quote(rcu_id)}/smartphones"
    headers = {"Accept": "application/json"}

    try:
        # GET ist für Listen der passendere Standard
        resp = requests.get(url, headers=headers, timeout=timeout_s)
        if resp.status_code == 405:
            # falls Backend fälschlich nur POST zulässt
            resp = requests.post(url, headers=headers, timeout=timeout_s)

        resp.raise_for_status()
        data = resp.json() or []

        # Sicherstellen, dass immer eine Liste zurückkommt
        if not isinstance(data, list):
            data = [data]

        cleaned = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            entry["deviceId"] = str(entry.get("deviceId", "")).strip().lower()
            cleaned.append(entry)

        print(f"[Cloud] {len(cleaned)} Smartphones von RCU {rcu_id} empfangen.")
        return cleaned

    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei Anfrage (get_assigned_smartphones): {e}")
        return []


    
"""
def get_target_manufacturer_id(rcu_id=RCU_ID, base_url = CLOUD_URL, timeout_s=10):
    
    Bestehende API für deviceId (bleibt erhalten).
    Nutzt intern get_assigned_smartphone.
    
    obj = get_assigned_smartphone(rcu_id=rcu_id, base_url=base_url, timeout_s=timeout_s)
    return obj.get("deviceId") if obj else None
    """

"""
def get_assigned_smartphone(rcu_id=RCU_ID, base_url = CLOUD_URL, timeout_s=10):
    
    rcu_id = str(rcu_id).strip()
    url = f"{base_url}/api/rcu/{quote(rcu_id)}/smartphones"
    headers = {"Accept": "application/json"}

    try:
        resp = requests.post(url, headers=headers, timeout=timeout_s)
        if resp.status_code == 405:
            resp = requests.get(url, headers=headers, timeout=timeout_s)

        resp.raise_for_status()
        data = resp.json() or {}
        # Erwartet mind. "id" und "deviceId"
        if "id" in data and "deviceId" in data:
            # Kleines Cleanup
            data["deviceId"] = str(data["deviceId"]).strip().lower()
            return data
        return None
    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei Anfrage: {e}")
        return None

"""