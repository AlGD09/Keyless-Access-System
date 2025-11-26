#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os 
import sys
import signal
import asyncio
import importlib
from ble import central
from ble import gatt_client
from ble.gatt_client import perform_challenge_response
from ble.gatt_client import send_unlock_status
from rcu_io.DIO6 import dio6_set
from bleak import BleakScanner
from config import CLOUD_URL
from config import RCU_ID

from cloud.api_client import get_assigned_smartphones  
from cloud.token_client import fetch_token_by_numeric_id, CloudError 
from cloud.notify import notify_rcu_event       
from cloud.remote_check import check_remote_mode
from auth.challenge import set_shared_key_hex
from unlocked.unlocked_mode import start_unlocked_mode
from remote.remote_mode import start_remote_mode



# RSSI-Schwelle für Freigabe (z. B. Gerät in Reichweite)
RSSI_THRESHOLD = -65  # dBm
RSSI_INTERVAL = 2      # Sekunden zwischen RSSI-Abfragen
RETRY_DELAY = 5       # Zeit zum Programm Neustart      
TIMEOUT = 5    # Scanning Zeit

NOT_FOUND = 3  # Versuche nach Authent. zum Neustart

async def monitor_rssi(address: str, selected_device_name, matched_device_id):
    """Überwacht die Signalstärke und steuert DIO6 entsprechend."""
    print(f"Starte RSSI-Überwachung für {address} (Schwelle: {RSSI_THRESHOLD} dBm)")

    not_found_count = 0  # Zähler für aufeinanderfolgende Nicht-Funde

    while True:
        try:
            # Kurzen Scan durchführen, um aktuellen RSSI des bekannten Geräts zu ermitteln
            devices = await BleakScanner.discover(timeout=2)
            rssi_value = None

            for d in devices:
                if d.address.lower() == address.lower():
                    rssi_value = d.rssi
                    break

            if rssi_value is not None:
                print(f"Aktueller RSSI: {rssi_value} dBm")

                if rssi_value > RSSI_THRESHOLD:
                    success = await send_unlock_status(address)
                    if success: 
                        notify_rcu_event(RCU_ID, selected_device_name, matched_device_id, 'Entriegelt')
                        print("[RSSI] Entsperr-Schwelle erreicht – verlasse RSSI-Überwachung.")
                        dio6_set(0)  # grün -> Freigabe
                        return True  # Zurück auf Main Loop + unlocked mode starten
                    else: 
                        print(f"Maschine bleibt verriegelt") # Erneut versuchen Nachricht an Smartphone
                        dio6_set(1) 
                else:
                    dio6_set(1)  # rot -> zu weit entfernt
                not_found_count = 0  # Zähler zurücksetzen
            else:
                print("Gerät im Scan nicht gefunden – vermutlich außer Reichweite.")
                dio6_set(1)  # Sicherheit: rot
                not_found_count += 1

                if not_found_count >= NOT_FOUND:
                    print("Gerät 3x in Folge nicht gefunden – starte Programm neu.")
                    os.execv(sys.executable, [sys.executable] + sys.argv)

            await asyncio.sleep(RSSI_INTERVAL)

        except Exception as e:
            print(f"Fehler beim RSSI-Check: {e}")
            dio6_set(1)
            return False

def init_devices_from_cloud(rcu_id=RCU_ID):
    """
    Lädt alle zugewiesenen Smartphones dieser RCU und deren Tokens.
    Rückgabe: Liste autorisierter Geräte mit Feldern:
        [
            {"id": 2, "deviceId": "6f0e2d2f34a1f4f8", "token": "<hexstring>"},
            ...
        ]
    Smartphones ohne gültiges Token werden übersprungen.
    """
    print(f"[RCU] Lade zugewiesene Smartphones für RCU {rcu_id} ...")
    smartphones = get_assigned_smartphones(rcu_id=rcu_id, base_url=CLOUD_URL)
    if not smartphones:
        raise RuntimeError("Keine Smartphones von der Cloud erhalten.")

    authorized = []
    for info in smartphones:
        numeric_id = info.get("id")
        device_id = info.get("deviceId")
        status = info.get("status")
        if not numeric_id or not device_id:
            continue

        if status == "active": 
            authorized.append({
                "id": numeric_id,
                "deviceId": device_id,
            })

    if not authorized:
        raise RuntimeError("Keine aktive Smartphones vorhanden - Scannen wird übersprungen")

    print(f"[CLOUD] {len(authorized)} autorisierte Geräte geladen.")
    return authorized



async def main():

    # Immer beim Keyboard Interrupt DIO -> 1 setzen
    def handle_sigint(signum, frame):
        dio6_set(1)
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_sigint)

    # --- MAIN-LOOP ---
    while True: 
        dio6_set(1)
        mode = check_remote_mode(RCU_ID)
        if mode:
            print("Starte Remote Mode...")
            start_remote_mode()
            print("Main Loop restartet")
            continue 



        print("Starte Verbindungsversuch...")

        try:
            authorized_devices = init_devices_from_cloud()
        except Exception as e:
            print(f"Cloud Verbindung fehlgeschlagen: {e}")
            dio6_set(1)
            await asyncio.sleep(RETRY_DELAY)
            continue

        importlib.reload(central)
        central.TARGET_DEVICE_BYTES_LIST = [bytes.fromhex(d["deviceId"]) for d in authorized_devices]
        print(f"[RCU] {len(central.TARGET_DEVICE_BYTES_LIST)} autorisierte Geräte an central übergeben.")


    
        selected_device, matched_device_id, scanner = await central.find_best_authorized_device(
            central.TARGET_DEVICE_BYTES_LIST, timeout=TIMEOUT
        )
        # selected_device, scanner = await central.find_target_device_keep_scanning(timeout=10)
        if not selected_device:
            print("Kein passendes Gerät gefunden. Neuer Versuch in wenigen Sekunden...")
            dio6_set(1)
            await asyncio.sleep(RETRY_DELAY)
            continue

        print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})") # z.B. Xiaomi 14T Pro (5A:74:B4:51:A5:A0)
        print(f"[RCU] matched deviceId: {matched_device_id}")  # z.B. 6f0e2d2f34a1f4f8

        matched_entry = next((d for d in authorized_devices if d["deviceId"] == matched_device_id), None)
        
        try: 
            token_hex = fetch_token_by_numeric_id(int(matched_entry["id"]))
            print(f"[CLOUD] Token für {selected_device.name} erhalten (id={matched_entry['id']}).")
        except CloudError as e:
            print(f"[CLOUD] Kein Token für {selected_device.name} erhalten: {e} – überspringe Verbindung.")
            dio6_set(1)
            await asyncio.sleep(RETRY_DELAY)
            continue

        set_shared_key_hex(token_hex)
        print(f"[RCU] Shared Key für deviceId={matched_device_id} gesetzt.")

        try:
            success = await perform_challenge_response(selected_device)  # Scanner läuft noch
        finally:
            if scanner:
                await scanner.stop()
        # print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})")

        # success = await perform_challenge_response(selected_device)

        if success:
            print("Authentifizierung erfolgreich – Freigabe aktiv.")
            # dio6_set(0) sofort grün
            notify_rcu_event(RCU_ID, selected_device.name, matched_device_id, 'Zugang autorisiert')
            result = await monitor_rssi(selected_device.address, selected_device.name, matched_device_id)
            if result:
                start_unlocked_mode(selected_device.name, matched_device_id)
            continue 

        else:
            print("Authentifizierung fehlgeschlagen – Zugang verweigert.")
            dio6_set(1)  # rot
            if gatt_client.RESPONSE_STATUS: # Falls doch ein Response erhalten wurde -> Fehler notify
                notify_rcu_event(RCU_ID, selected_device.name, matched_device_id, 'Zugang verweigert')

            await asyncio.sleep(RETRY_DELAY)
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as e:
        # Wenn der Exit-Code der bekannte BlueZ-Fehler ist → Neustart
        if "org.bluez.GattService1" in str(e):
            print("BlueZ-GattService-Fehler erkannt – starte Programm neu ...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            # andere SystemExit-Fälle normal beenden
            raise
    except KeyboardInterrupt:
        dio6_set(1)  
        sys.exit(1)
    except Exception as e:
        dio6_set(1)
        # andere Ausnahmen nur anzeigen
        print(f"Unerwarteter Fehler: {e}")
        raise