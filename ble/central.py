#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU (nur Funktionen, kein direkter Start)
"""

from bleak import BleakScanner, BleakClient
import asyncio

TARGET_MANUFACTURER_ID = 0xFFFF
EXPECTED_PAYLOAD = b""


async def scan_for_devices(timeout: int = 10):
    """Scannt nach Geräten mit der passenden Manufacturer Data."""
    print(f"🔍 Scanning for BLE devices for {timeout} s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []

    for d in devices:
        name = d.name or "N/A"
        mdata = d.metadata.get("manufacturer_data", {})

        if not mdata:
            continue

        for comp_id, payload in mdata.items():
            if comp_id == TARGET_MANUFACTURER_ID:
                if not EXPECTED_PAYLOAD or payload.startswith(EXPECTED_PAYLOAD):
                    print(f"✅ Matching device: {name} ({d.address})")
                    found.append(d)
    return found


async def connect_to_device(device):
    """Verbindet zur angegebenen Adresse und zeigt GATT-Services."""
    print(f"🔗 Connecting to {device.name or 'N/A'} ({device.address}) ...")
    try:
        async with BleakClient(device.address) as client:
            if client.is_connected:
                print(f"✅ Connected to {device.name or 'N/A'}")
                for service in client.services:
                    print(f"[Service] {service.uuid}")
                    for char in service.characteristics:
                        print(f"  [Characteristic] {char.uuid} (props: {char.properties})")
                print("🔌 Disconnecting ...")
            else:
                print("❌ Connection failed.")
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
