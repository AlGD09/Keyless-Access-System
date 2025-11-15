# /cloud/notify.py

import requests
import json
from config import CLOUD_URL
from config import RCU_ID


def notify_rcu_event(rcu_id=RCU_ID, deviceName: str = 'none', deviceId: str = 'None', result: str = 'none', base_url=CLOUD_URL, timeout_s=10):

    rcu_id = str(rcu_id).strip()
    url = f"{base_url}/api/rcu/events/add"
    headers = {"Content-Type": "application/json"}

    if deviceName == "BlueZ 5.72":
        deviceName = "Laptop-phone"

    payload = {
        "rcuId": RCU_ID,
        "deviceName": deviceName, 
        "deviceId": deviceId,
        "result": result
    }

    try: 
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        r.raise_for_status()
        print(f"[Cloud] Event notified.")
    except requests.RequestException as e:
        print(f"[Cloud] Fehler bei Zustandsbenachrichtigung: {e}")
        return []
