#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU (Modul)
Erkennt Geräte anhand ihrer Manufacturer Data (Company Identifier + Payload)
und verbindet sich automatisch mit ihnen.
"""

from bleak import BleakScanner, BleakClient
import asyncio

# Gesuchter Manufacturer Identifier (16-bit Company ID)
TARGET_MANUFACTURER_ID = 0xFFFF
# Optional: erwarteter Payload (leer = egal)
EXPECTED_PAYLOAD = b""


async def scan_for_devices(timeout: int = 10):
    """Scannt BLE-Geräte und gibt passende Geräte inkl. Manufacturer Data zurück."""
    print(f"🔍 Scanning for BLE devices for {timeout} s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []

    for d in devices:
        name = d.name or "N/A"
        mdata = d.metadata.get("manufacturer_data", {})

        if not mdata:
            continue

        for comp_id, payload in mdata.items():
            # Alle Manufacturer-Daten anzeigen
            print(f"📡 {name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload.hex()}")

            if comp_id == TARGET_MANUFACTURER_ID:
                if not EXPECTED_PAYLOAD or payload.startswith(EXPECTED_PAYLOAD):
                    print(f"✅ Matching device gefunden: {name} ({d.address})")
                    found.append({
                        "device": d,
                        "company_id": comp_id,
                        "payload": payload
                    })
    return found


async def connect_to_device(device):
    """Verbindet zu einem Gerät und zeigt dessen GATT-Services an."""
    d = device["device"]
    print(f"🔗 Connecting to {d.name or 'N/A'} ({d.address}) ...")

    try:
        async with BleakClient(d.address) as client:
            if client.is_connected:
                print(f"✅ Connected to {d.name or 'N/A'} ({d.address})")
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
