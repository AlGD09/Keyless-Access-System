# /remote/remote_mode.py
import time 
import requests
from rcu_io.DIO6 import dio6_set
from cloud.notify import notify_rcu_event  
from config import CLOUD_URL, RCU_ID





def start_remote_mode(): 

    print("\n[RCU] >>> REMOTE-MODE AKTIV <<<")
    print("[RCU] Warte auf Befehle von der Cloud...\n")


    sse_url = f"{CLOUD_URL}/api/rcu/remote/sse/{RCU_ID}"
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    while True: 
        try: 
            with requests.get(sse_url, headers=headers, stream=True, timeout=(5, 15)) as resp:
                for raw_line in resp.iter_lines(decode_unicode=True):

                    # LOG COMPLETO
                    print(f"[RAW SSE] >> '{raw_line}'")

                    if not raw_line:
                        continue

                    line = raw_line

                    if line.startswith("data:"):
                        # Limpieza robusta
                        cleaned = line.replace("data:", "").strip()
                        event = cleaned.upper()

                        print(f"[UNLOCKED][SSE] Event: '{event}'")

                        if event == "LOCK":
                            print("\n[RCU] >>> LOCK von der Cloud erhalten – Maschine wird verriegelt <<<")
                            dio6_set(1)
                            notify_rcu_event(RCU_ID, 'Remote Control', '1', 'Remote Verriegelt')
                        
                        if event == "UNLOCK":
                            print("\n[RCU] >>> UNLOCK von der Cloud erhalten – Maschine wird entriegelt <<<")
                            dio6_set(0)
                            notify_rcu_event(RCU_ID, 'Remote Control', '1', 'Remote Entriegelt')
                        
                        if event == "EXIT":
                            print("\n[RCU] >>> EXIT von der Cloud erhalten – Remote Mode wird verlassen <<<")
                            dio6_set(1)
                            notify_rcu_event(RCU_ID, 'Remote Control', '1', 'Fernsteuerung deaktiviert')
                            time.sleep(1)
                            return # <-- kehrt zu main() zurück
                        
        except Exception as e:
            print("\n[REMOTE][FAILSAFE] Cloud-Verbindung dauerhaft verloren – Maschine wird verriegelt!\n") 
            dio6_set(1)
            return # <-- kehrt zu main() zurück
                        





