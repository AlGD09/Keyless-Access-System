#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from ble.central import scan_for_devices
from ble.gatt_client import perform_challenge_response
from rcu_io.DIO6 import dio6_set
from bleak import BleakScanner

# RSSI-Schwelle für Freigabe (z. B. Gerät in Reichweite)
RSSI_THRESHOLD = -80   # dBm
RSSI_INTERVAL = 3      # Sekunden zwischen RSSI-Abfragen


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
            break


async def main():
    print("Starte Keyless-Access-System (BLE Central)...")
    found_devices = await scan_for_devices(timeout=10)
    if not found_devices:
        print("Kein passendes Gerät gefunden.")
        return

    selected_device = found_devices[0]["device"]
    print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})")

    success = await perform_challenge_response(selected_device)

    if success:
        print("Authentifizierung erfolgreich – Freigabe aktiv.")
        dio6_set(0)  # sofort grün
        await monitor_rssi(selected_device.address)
    else:
        print("Authentifizierung fehlgeschlagen – Zugang verweigert.")
        dio6_set(1)  # rot


if __name__ == "__main__":
    asyncio.run(main())
