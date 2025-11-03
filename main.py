#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os 
import sys
import asyncio
import importlib
from ble import central
from ble.gatt_client import perform_challenge_response
from rcu_io.DIO6 import dio6_set
from bleak import BleakScanner
from config import CLOUD_URL

from cloud.api_client import get_assigned_smartphones  
from cloud.token_client import fetch_token_by_numeric_id, CloudError        
from auth.challenge import set_shared_key_hex



# RSSI-Schwelle für Freigabe (z. B. Gerät in Reichweite)
RSSI_THRESHOLD = -65  # dBm
RSSI_INTERVAL = 3      # Sekunden zwischen RSSI-Abfragen
RETRY_DELAY = 10

async def monitor_rssi(address: str):
    """Überwacht die Signalstärke und steuert DIO6 entsprechend."""
    print(f"Starte RSSI-Überwachung für {address} (Schwelle: {RSSI_THRESHOLD} dBm)")

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
                    dio6_set(0)  # grün → Freigabe
                else:
                    dio6_set(1)  # rot → zu weit entfernt
            else:
                print("Gerät im Scan nicht gefunden – vermutlich außer Reichweite.")
                dio6_set(1)  # Sicherheit: rot

            await asyncio.sleep(RSSI_INTERVAL)

        except Exception as e:
            print(f"Fehler beim RSSI-Check: {e}")
            dio6_set(1)
            break###

"""
def init_shared_key_from_cloud() -> str:
    
    info = get_assigned_smartphone(rcu_id="A116G61", base_url = CLOUD_URL)
    if not info:
        raise RuntimeError("Kein zugewiesenes Smartphone erhalten.")

    numeric_id = info["id"]        # für Token-Endpoint
    device_id  = info["deviceId"]  

    try:
        token_hex = fetch_token_by_numeric_id(int(numeric_id))  # holt Hex-String
    except CloudError as e:
        raise RuntimeError(f"Token konnte nicht geladen werden: {e}") from e

    set_shared_key_hex(token_hex)
    print(f"Shared Key gesetzt (from cloud). deviceId={device_id}, id={numeric_id}")
    return device_id
"""

def init_devices_from_cloud(rcu_id="A116G61"):
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
        if not numeric_id or not device_id:
            continue

        try:
            token_hex = fetch_token_by_numeric_id(int(numeric_id))
            authorized.append({
                "id": numeric_id,
                "deviceId": device_id,
                "token": token_hex
            })
            print(f"[RCU] Token für deviceId={device_id} erhalten (id={numeric_id}).")
        except CloudError as e:
            print(f"[RCU] Kein Token für deviceId={device_id}: {e}")

    if not authorized:
        raise RuntimeError("Keine gültigen Tokens für zugewiesene Smartphones gefunden.")

    print(f"[RCU] {len(authorized)} autorisierte Geräte geladen.")
    return authorized



async def main():
    while True: 
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
            central.TARGET_DEVICE_BYTES_LIST, timeout=10
        )
        # selected_device, scanner = await central.find_target_device_keep_scanning(timeout=10)
        if not selected_device:
            print("Kein passendes Gerät gefunden. Neuer Versuch in wenigen Sekunden...")
            dio6_set(1)
            await asyncio.sleep(RETRY_DELAY)
            continue

        print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})")
        print(f"[RCU] matched deviceId: {matched_device_id}")

        matched_entry = next((d for d in authorized_devices if d["deviceId"] == matched_device_id), None)
        if not matched_entry:
            print(f"[RCU] Kein Token für deviceId={matched_device_id} gefunden – überspringe Verbindung.")
            dio6_set(1)
            await asyncio.sleep(RETRY_DELAY)
            continue

        set_shared_key_hex(matched_entry["token"])
        print(f"[RCU] Shared Key für deviceId={matched_device_id} gesetzt.")

        try:
            success = await perform_challenge_response(selected_device)  # Scanner läuft noch!
        finally:
            if scanner:
                await scanner.stop()
        # print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})")

        # success = await perform_challenge_response(selected_device)

        if success:
            print("Authentifizierung erfolgreich – Freigabe aktiv.")
            dio6_set(0)  # sofort grün
            await monitor_rssi(selected_device.address)
        else:
            print("Authentifizierung fehlgeschlagen – Zugang verweigert.")
            dio6_set(1)  # rot
            await asyncio.sleep(RETRY_DELAY)
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as e:
        # Wenn der Exit-Code der bekannte BlueZ-Fehler ist → Neustart
        if "org.bluez.GattService1" in str(e):
            print("🔁 BlueZ-GattService-Fehler erkannt – starte Programm neu ...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            # andere SystemExit-Fälle normal beenden
            raise
    except Exception as e:
        # andere Ausnahmen nur anzeigen
        print(f"Unerwarteter Fehler: {e}")
        raise