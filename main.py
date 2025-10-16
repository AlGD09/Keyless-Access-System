#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py – zentrales Steuerprogramm der RCU
Startet BLE-Scanning und Verbindung (Central-Logik)
"""

import asyncio
from ble.central import scan_for_devices, connect_to_device


async def main():
    print("🚗 Starte Keyless-Access-System (BLE Central)...")

    # Scan nach Geräten mit passender Manufacturer Data
    found_devices = await scan_for_devices(timeout=10)

    if not found_devices:
        print("❌ Kein passendes Gerät gefunden.")
        return

    print("\n📋 Gefundene Geräte mit passender Manufacturer Data:")
    for idx, info in enumerate(found_devices, start=1):
        d = info["device"]
        cid = info["company_id"]
        payload = info["payload"]
        print(f" {idx}. {d.name or 'N/A'} ({d.address})")
        print(f"    → Company ID: 0x{cid:04X}")
        print(f"    → Payload   : {payload.hex()}")
    print("")

    # Verbindung zu jedem Gerät herstellen
    for info in found_devices:
        await connect_to_device(info)
        print("—" * 40)
        await asyncio.sleep(2)

    print("✅ Scan-Durchlauf abgeschlossen.")


if __name__ == "__main__":
    asyncio.run(main())
