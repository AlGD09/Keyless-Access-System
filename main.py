#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py – zentrales Steuerprogramm der RCU
Startet BLE-Scanning und führt den Challenge-Response-Prozess aus.
"""

import asyncio
from ble.central import scan_for_devices
from ble.gatt_client import perform_challenge_response


async def main():
    print("Starte Keyless-Access-System (BLE Central)...")

    # Scanne nach Geräten mit passender Manufacturer Data
    found_devices = await scan_for_devices(timeout=10)

    if not found_devices:
        print("Kein passendes Gerät gefunden.")
        return

    print("\nGefundene Geräte mit passender Manufacturer Data:")
    for idx, info in enumerate(found_devices, start=1):
        d = info["device"]
        cid = info["company_id"]
        payload = info["payload"]
        print(f" {idx}. {d.name or 'N/A'} ({d.address})")
        print(f"    → Company ID: 0x{cid:04X}")
        print(f"    → Payload   : {payload.hex()}")
    print("")

    # Wähle erstes gefundenes Gerät aus (du kannst später Auswahl erweitern)
    selected_device = found_devices[0]["device"]
    print(f"Verwende Gerät: {selected_device.name or 'N/A'} ({selected_device.address})")

    # Führe Challenge-Response-Prozess aus
    success = await perform_challenge_response(selected_device)

    # Reaktion je nach Ergebnis
    if success:
        print("Authentifizierung erfolgreich – Zugang freigegeben.")
    else:
        print("Authentifizierung fehlgeschlagen – Zugang verweigert.")

    print("\nProzess abgeschlossen.")


if __name__ == "__main__":
    asyncio.run(main())
