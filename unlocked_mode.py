# unlocked_mode.py
import time
import requests
import threading
import asyncio

from bleak import BleakScanner, BleakClient
from rcu_io.DIO6 import dio6_set
from config import CLOUD_URL, RCU_ID

SSE_RECONNECT_DELAY = 2
SSE_TIMEOUT = 300  # Verbindung wird jede x Sekunden erneuert 
FAILSAFE_TIMEOUT = 30   # Sekunden bis Auto-Lock, wenn Cloud tot ist


RSSI_UNLOCK_THRESHOLD = -90     # wenn darunter → sperren
RSSI_CHECK_INTERVAL = 3         # Sekunden Abstand 

def start_unlocked_mode(selected_device_name, selected_device_adress, matched_device_id):
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

    stop_flag = threading.Event()

    watchdog = threading.Thread(
        target=rssi_watchdog,
        args=(selected_device_adress, selected_device_name, matched_device_id, stop_flag),
        daemon=True
    )
    watchdog.start()

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
                            stop_flag.set()
                            return handle_lock(selected_device_name, matched_device_id)  
                            


        except Exception as e:
            print(f"[UNLOCKED][SSE] Verbindung verloren – neuer Versuch in {SSE_RECONNECT_DELAY}s. Fehler: {e}") # Falls Verbindung fehlschlägt, wieder in 2s versuchen
            if time.time() - failsafe_start > FAILSAFE_TIMEOUT:
                print("\n[UNLOCKED][FAILSAFE] Cloud-Verbindung dauerhaft verloren – Maschine wird verriegelt!\n")
                stop_flag.set()
                return handle_lock(selected_device_name, matched_device_id)

            # sonst normal warten und weiter versuchen
            time.sleep(SSE_RECONNECT_DELAY)


def handle_lock(selected_device_name, matched_device_id):
    """
    LOCK von der Cloud empfangen:
    - Maschine verriegeln
    - LED auf rot setzen
    - Modus verlassen -> main() übernimmt wieder
    """

    print("\n[RCU] >>> LOCK von der Cloud erhalten – Maschine wird verriegelt <<<")

    # Verriegeln
    dio6_set(1)

    # Optional: Cloud über Verriegelung informieren
    # notify_rcu_event(RCU_ID, selected_device_name, matched_device_id, 'Verriegelt')

    # Kleine Pause für Hardware-Stabilität
    time.sleep(1)

    print("[RCU] Maschine verriegelt. Rückkehr zum Scan-Modus.\n")
    return  # <-- kehrt zu main() zurück


def rssi_watchdog(address, selected_device_name, matched_device_id, stop_flag):
    asyncio.run(rssi_watchdog_coroutine(
        address,
        selected_device_name,
        matched_device_id,
        stop_flag
    ))

async def rssi_watchdog_coroutine(address, selected_device_name, matched_device_id, stop_flag):
    print("[RSSI] Watchdog gestartet.")

    while not stop_flag.is_set():
        try:
            client = BleakClient(address, timeout=6.0, adapter="hci0")

            await client.connect()
            if not client.is_connected:
                print("[RSSI] Verbindung nicht möglich.")
                await asyncio.sleep(2)
                continue

            # RSSI lesen
            rssi = await client.get_current_rssi()
            await client.disconnect()

            if rssi is not None:
                print(f"[RSSI] {rssi} dBm")

            if rssi < RSSI_UNLOCK_THRESHOLD:
                print("[RSSI] Schwelle unterschritten → AUTO-LOCK")
                stop_flag.set()
                handle_lock(selected_device_name, matched_device_id)
                return

            await asyncio.sleep(RSSI_CHECK_INTERVAL)

        except Exception as e:
            print(f"[RSSI] Fehler: {e}")
            await asyncio.sleep(2)

