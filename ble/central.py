#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU
Erkennt Geräte anhand ihrer Manufacturer Data (Company Identifier + Payload)
und verbindet sich automatisch mit ihnen.
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Gesuchter Manufacturer Identifier (16-bit Company ID)
# z. B. 0xFFFF = Testwert aus nRF Connect Advertising "Manufacturer Data"
TARGET_MANUFACTURER_ID = 0xFFFF

# Optional: erwarteter Inhalt im Payload (als Bytefolge)
EXPECTED_PAYLOAD = b""  # Beispielinhalt


async def scan_for_devices(timeout: int = 10):
    """
    Scannt BLE-Geräte und prüft, ob Manufacturer Data den gewünschten Identifier enthält.
    """
    print(f"🔍 Scanning for BLE devices for {timeout} s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []

    for d in devices:
        name = d.name or "N/A"
        mdata = d.metadata.get("manufacturer_data", {})

        if not mdata:
            print(f"• Skipped: {name} ({d.address}) – keine Manufacturer Data")
            continue

        for comp_id, payload in mdata.items():
            print(f"📡 {name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload.hex()}")

            if comp_id == TARGET_MANUFACTURER_ID:
                # Optional: prüfe zusätzlich, ob Payload passt
                if not EXPECTED_PAYLOAD or payload.startswith(EXPECTED_PAYLOAD):
                    print(f"✅ Matching device gefunden: {name} ({d.address})")
                    found.append(d)
                else:
                    print(f"⚠️ Hersteller-ID stimmt, aber Payload passt nicht.")

    return found


async def connect_to_device(device):
    """
    Baut eine Verbindung auf und listet Services & Characteristics.
    """
    print(f"🔗 Connecting to {device.name or 'N/A'} ({device.address}) ...")
    try:
        async with BleakClient(device.address) as client:
            if client.is_connected:
                print(f"✅ Connected to {device.name or 'N/A'} ({device.address})")
                print("🔎 Discovering services ...")

                for service in client.services:
                    print(f"[Service] {service.uuid}")
                    for char in service.characteristics:
                        print(f"  [Characteristic] {char.uuid} (props: {char.properties})")

                print("🔌 Disconnecting ...")
            else:
                print("❌ Connection failed.")
    except Exception as e:
        print(f"⚠️ Connection error: {e}")


async def main():
    found_devices = await scan_for_devices(timeout=10)
    if not found_devices:
        print("❌ Kein Gerät mit passender Manufacturer Data gefunden.")
        return

    for dev in found_devices:
        await connect_to_device(dev)
        print("—" * 40)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
