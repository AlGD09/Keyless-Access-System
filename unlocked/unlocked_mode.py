# unlocked_mode.py
import time
import requests
from rcu_io.DIO6 import dio6_set
from unlocked.distance_check import start_advertising_thread, stop_advertising_thread
from config import CLOUD_URL, RCU_ID

SSE_RECONNECT_DELAY = 2
SSE_TIMEOUT = 300  # Verbindung wird jede x Sekunden erneuert 
FAILSAFE_TIMEOUT = 30   # Sekunden bis Auto-Lock, wenn Cloud tot ist


def start_unlocked_mode(selected_device_name, matched_device_id):
    """
    Dieser Modus wird nach erfolgreicher BLE + RSSI-Freigabe betreten.
    Die Maschine ist entsperrt und wartet auf LOCK von der Cloud.
    Bei LOCK wird verriegelt und die Funktion beendet -> main() läuft weiter.
    """

    print("\n[RCU] >>> ENTSPERRT-MODUS AKTIV <<<")
    print("[RCU] Maschine ist freigegeben. Warte auf LOCK von der Cloud...\n")

    failsafe_start = time.time()

    # Maschine ist offen → LED grün
    dio6_set(0)

    # container, loop = start_advertising_thread()

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
            with requests.get(sse_url, headers=headers, stream=True, timeout=None) as resp:  
                for raw_line in resp.iter_lines(decode_unicode=True): # Cloud sendet Zeilen wie: data: LOCK, data: HEARTBEAT_OK, data: STATUS
                    
                    if not raw_line:
                        continue

                    line = raw_line   # Bytes in Strings dekodieren in data 

                    if line.startswith("data:"):
                        event = line.split(":", 1)[1].strip()  # schneidet "data: " von der Nachricht
                        print(f"[UNLOCKED][SSE] Event: {event}")

                        if event == "LOCK":  # Falls LOCK empfangen wird, Maschine verriegeln (DIO-1) und zurücl zu Main (Scannen)     
                            return handle_lock(container, loop)  

        except Exception as e:
            print(f"[UNLOCKED][SSE] Verbindung verloren – neuer Versuch in {SSE_RECONNECT_DELAY}s. Fehler: {e}") # Falls Verbindung fehlschlägt, wieder in 2s versuchen
            if time.time() - failsafe_start > FAILSAFE_TIMEOUT:
                print("\n[UNLOCKED][FAILSAFE] Cloud-Verbindung dauerhaft verloren – Maschine wird verriegelt!\n") 
                return handle_lock(container, loop)

            # sonst normal warten und weiter versuchen
            time.sleep(SSE_RECONNECT_DELAY)


def handle_lock(container, loop):

    print("\n[RCU] >>> LOCK von der Cloud erhalten – Maschine wird verriegelt <<<")
    # Verriegeln
    dio6_set(1)
    # Optional: Cloud über Verriegelung informieren
    # notify_rcu_event(RCU_ID, selected_device_name, matched_device_id, 'Verriegelt')

    # Kleine Pause für Hardware-Stabilität
    time.sleep(1)

    # stop_advertising_thread(container, loop)

    print("[RCU] Maschine verriegelt. Rückkehr zum Scan-Modus.\n")
    return  # <-- kehrt zu main() zurück




