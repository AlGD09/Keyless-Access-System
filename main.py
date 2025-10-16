#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from ble.central import scan_for_devices
from ble.gatt_client import perform_challenge_response
from rcu_io.DIO6 import dio6_set
from bleak import BleakClient

# RSSI-Schwelle für Freigabe (z. B. Gerät in Reichweite)
RSSI_THRESHOLD = -80  # dBm
RSSI_INTERVAL = 3     # Sekunden zwischen RSSI-Abfragen

async def monitor_rssi(address: str):
    """Überwacht die Signalstärke und steuert DIO6 entsprechend."""
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("Keine aktive Verbindung zur RSSI-Überwachung.")
            return

        print(f"Starte RSSI-Überwachung für {address} (Schwelle: {RSSI_THRESHOLD} dBm)")
        while True:
            try:
                rssi = await client.get_rssi()
                print(f"Aktueller RSSI: {rssi} dBm")

                if rssi is not None and rssi > RSSI_THRESHOLD:
                    dio6_set(0)  # grün (Freigabe)
                else:
                    dio6_set(1)  # rot (zu weit entfernt)

                await asyncio.sleep(RSSI_INTERVAL)

            except Exception as e:
                print(f"Fehler beim RSSI-Check: {e}")
                dio6_set(1)  # Sicherheit: Sperre aktivieren
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
