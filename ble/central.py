#!/usr/bin/env python3
# ble/central.py – BLE Central-Logik der RCU
# Scannt nach bekannten Geräten (Smartphones) und stellt Verbindung her

import asyncio
from bleak import BleakScanner, BleakClient

# Whitelist der bekannten Geräte (z. B. Smartphone-Adressen oder Namen)
WHITELIST = {
    "E8:98:47:54:07:79": "Xiaomi 14T Pro",
    "D4:3A:2C:11:22:33": "TestPhone_2"
}

# Optional: UUID eines Services, nach dem gefiltert werden soll
TARGET_SERVICE_UUID = "12345678-0000-1000-8000-00805f9b34fb"

async def scan_for_devices(timeout: int = 10):
    """
    Scannt die Umgebung nach BLE-Advertisings und gibt gefundene Geräte zurück.
    """
    print(f"🔍 Scanning for BLE devices for {timeout} seconds...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []
    for d in devices:
        name = d.name or "N/A"
        if d.address in WHITELIST or name in WHITELIST.values():
            print(f"✅ Found whitelisted device: {name} ({d.address})")
            found.append(d)
        else:
            print(f"• Skipped: {name} ({d.address})")
    return found

async def connect_to_device(device):
    """
    Baut eine Verbindung zu einem gefundenen BLE-Gerät auf.
    """
    print(f"🔗 Connecting to {device.name} ({device.address})...")
    try:
        async with BleakClient(device.address) as client:
            if client.is_connected:
                print(f"✅ Connected to {device.name} ({device.address})")
                print("🔎 Discovering services...")
                for service in client.services:
                    print(f"  [Service] {service.uuid}")
                    for char in service.characteristics:
                        print(f"    [Characteristic] {char.uuid} (props: {char.properties})")

                print("🔌 Disconnecting...")
            else:
                print("❌ Connection failed.")
    except Exception as e:
        print(f"⚠️ Connection error: {e}")

async def main():
    found_devices = await scan_for_devices(timeout=8)
    if not found_devices:
        print("❌ No whitelisted devices found.")
        return

    for dev in found_devices:
        await connect_to_device(dev)
        print("—" * 40)
        # Optional: Warte kurz zwischen mehreren Verbindungen
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
