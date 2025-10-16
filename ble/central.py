#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU
Erkennt Geräte anhand beworbener Service-UUIDs (statt MAC oder Name)
und verbindet sich automatisch mit ihnen.
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Gesuchte Service-UUID (aus nRF Connect: 0x12345678)
TARGET_SERVICE_UUID = "12345678-0000-1000-8000-00805f9b34fb"


async def scan_for_devices(timeout: int = 10):
    """
    Scannt die Umgebung nach BLE-Geräten, prüft deren Advertised Service UUIDs
    und gibt passende Geräte zurück.
    """
    print(f"🔍 Scanning for BLE devices for {timeout} s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []

    for d in devices:
        name = d.name or "N/A"
        uuids = [u.lower() for u in d.metadata.get("uuids", [])]

        if TARGET_SERVICE_UUID.lower() in uuids:
            print(f"✅ Found target UUID on device: {name} ({d.address})")
            print(f"   → Advertised UUIDs: {uuids}")
            found.append(d)
        else:
            print(f"• Skipped: {name} ({d.address}) – UUIDs: {uuids or 'none'}")

    return found


async def connect_to_device(device):
    """
    Baut eine Verbindung zu einem Gerät auf und listet seine Services/Characteristics.
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
    # Suche nach Geräten, die die Ziel-UUID bewerben
    found_devices = await scan_for_devices(timeout=10)
    if not found_devices:
        print("❌ No devices advertising the target UUID found.")
        return

    # Verbinde dich mit jedem gefundenen Gerät
    for dev in found_devices:
        await connect_to_device(dev)
        print("—" * 40)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
