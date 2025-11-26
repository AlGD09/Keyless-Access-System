# unlocked_mode.py
import time
import requests
from rcu_io.DIO6 import dio6_set
from unlocked.distance_check import start_advertising_thread, stop_advertising_thread
from cloud.notify import notify_rcu_event   
from config import CLOUD_URL, RCU_ID





def start_unlocked_mode(selected_device_name, matched_device_id):
    """
    Dieser Modus wird nach erfolgreicher BLE + RSSI-Freigabe betreten.
    Die Maschine ist entsperrt und wartet auf LOCK von der Cloud.
    Bei LOCK wird verriegelt und die Funktion beendet -> main() läuft weiter.
    """

    print("\n[RCU] >>> ENTSPERRT-MODUS AKTIV <<<")
    print("[RCU] Maschine ist freigegeben. Warte auf LOCK von der Cloud...\n")


    # Maschine ist offen → LED grün
    dio6_set(0)

    #
    container, loop = start_advertising_thread()

    # SSE-Endpunkt der Cloud
    sse_url = f"{CLOUD_URL}/api/rcu/sse/{RCU_ID}"
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    while True:  # Endlos-Schleide -> verbunden bleiben
        try:   # Verbindung offen bleiben Cloud "LOCK" sendet, oder Verbindung verloren
            # Persistente SSE-Verbindung zur Cloud starten
            with requests.get(sse_url, headers=headers, stream=True, timeout=(5, 15)) as resp: ## 5s Verbindungsaufbau, 15s max. Wartezeit zwischen Daten
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
                            return handle_lock(container, loop, selected_device_name, matched_device_id)

        except Exception as e:
            print("\n[UNLOCKED][FAILSAFE] Cloud-Verbindung dauerhaft verloren – Maschine wird verriegelt!\n") 
            # stop_advertising_thread(container, loop)
            return handle_lock(container, loop, selected_device_name, matched_device_id)

        



def handle_lock(container, loop, selected_device_name, matched_device_id):

    print("\n[RCU] >>> LOCK von der Cloud erhalten – Maschine wird verriegelt <<<")
    # Verriegeln
    dio6_set(1)
    # Optional: Cloud über Verriegelung informieren
    notify_rcu_event(RCU_ID, selected_device_name, matched_device_id, 'Verriegelt')
    stop_advertising_thread(container, loop)
    # Kleine Pause für Hardware-Stabilität
    time.sleep(1)

    print("[RCU] Maschine verriegelt. Rückkehr zum Scan-Modus.\n")
    return  # <-- kehrt zu main() zurück




