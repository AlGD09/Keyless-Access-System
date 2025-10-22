# /cloud/api_client.py
import requests
from urllib.parse import quote

def get_assigned_smartphone(rcu_id="A116G61", base_url="http://10.42.0.1:8080", timeout_s=4):
    """
    Fragt die Cloud nach dem zugewiesenen Smartphone und gibt das gesamte JSON-Objekt zurück,
    z.B.: {"id": 2, "deviceId": "bd45e75870af93c2", ...}
    """
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


def get_target_manufacturer_id(rcu_id="A116G61", base_url="http://10.42.0.1:8080", timeout_s=4):
    """
    Bestehende API für deviceId (bleibt erhalten).
    Nutzt intern get_assigned_smartphone.
    """
    obj = get_assigned_smartphone(rcu_id=rcu_id, base_url=base_url, timeout_s=timeout_s)
    return obj.get("deviceId") if obj else None