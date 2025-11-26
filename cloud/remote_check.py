# /cloud/remote_check.py

import requests
import json
from urllib.parse import quote
from config import CLOUD_URL
from config import RCU_ID



def check_remote_mode(rcu_id=RCU_ID): 

    rcu_id = str(rcu_id).strip()
    url = f"{CLOUD_URL}/api/rcu/status/{quote(rcu_id)}"
    headers = {"Accept": "application/json"}

    try: 
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        print(f"[Cloud] Remote Status angefragt.")

    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei der Status-Anfrage: {e}")
        return []
    
    status_raw = "" 
    body = (resp.text or "").strip()

    # --- JSON lesen, falls möglich ---
    try:
        js = resp.json()
        if isinstance(js, dict):
            if "status" in js:
                status_raw = str(js["status"]).strip()
    except Exception:
        pass

    # Fallback, falls kein JSON erkannt wurde
    if not status_raw and body:
        status_raw = body
        status_raw = status_raw.strip()

    if not status_raw:
        print(f"Kein Status erhalten")
        return False
    elif status_raw == "remote mode requested": 
        return True # REMOTE MODE starten
    else: 
        return False



