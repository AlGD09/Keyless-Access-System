#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU (Modul)
Erkennt Geräte anhand ihrer Manufacturer Data (Company Identifier + Payload)
und liefert die Treffer an main.py zurück (main steuert Connect/Challenge).
"""

import asyncio
from bleak import BleakScanner, BleakClient
from cloud.api_client import get_target_manufacturer_id

# ---------------------------------------------------------
# Zielparameter aus Cloud laden (Device-ID des Smartphones)
# ---------------------------------------------------------
TARGET_DEVICE_ID = get_target_manufacturer_id()  # z. B. "bd45e75870af93c2"
if TARGET_DEVICE_ID:
    print(f"[BLE] Ziel-Device-ID aus Cloud: {TARGET_DEVICE_ID}")
    try:
        TARGET_DEVICE_BYTES = bytes.fromhex(TARGET_DEVICE_ID)
    except ValueError:
        print("[BLE] Ungültige Device-ID (kein Hex). Deaktiviere Payload-Filter.")
        TARGET_DEVICE_BYTES = None
else:
    print("[BLE] Keine gültige Device-ID erhalten – Payload-Filter deaktiviert (keine Verbindung).")
    TARGET_DEVICE_BYTES = None

# Gesuchter Manufacturer Identifier (16-bit Company ID)
TARGET_MANUFACTURER_ID = 0xFFFF


async def scan_for_devices(timeout: int = 10):
    """
    Scannt BLE-Geräte und gibt passende Geräte inkl. Manufacturer Data zurück.
    Ein Gerät ist 'passend', wenn:
      - Company ID == 0xFFFF und
      - TARGET_DEVICE_BYTES im Payload enthalten ist.
    HINWEIS: Wenn keine TARGET_DEVICE_BYTES vorliegen, wird NICHT gematcht.
    """
    print(f"🔍 Scanning for BLE devices for {timeout} s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    found = []

    for d in devices:
        name = d.name or "N/A"
        # Hinweis: metadata ist in neueren Bleak-Versionen deprecated – für jetzt ausreichend.
        mdata = d.metadata.get("manufacturer_data", {})
        if not mdata:
            continue

        for comp_id, payload in mdata.items():
            try:
                payload_hex = payload.hex()
            except Exception:
                payload_hex = str(payload)

            print(f"📡 {name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload_hex}")

            # 1) nur 0xFFFF
            if comp_id != TARGET_MANUFACTURER_ID:
                continue

            # 2) striktes Payload-Matching: ohne Cloud-ID verbinden wir NICHT
            if TARGET_DEVICE_BYTES is None:
                print("↪︎ 0xFFFF gesehen, aber keine Device-ID verfügbar → überspringe.")
                continue

            if TARGET_DEVICE_BYTES not in payload:
                print("↪︎ 0xFFFF passt, aber Device-ID nicht im Payload → überspringe.")
                continue

            print(f"✅ Matching device gefunden: {name} ({d.address})")
            found.append({
                "device": d,
                "company_id": comp_id,
                "payload": payload
            })

    return found


async def connect_to_device(device):
    """
    Optional: direkter Connect + Servicelisting (wird von main.py aktuell nicht genutzt,
    aber behalten wir für Debug).
    """
    d = device["device"]
    print(f"🔗 Connecting to {d.name or 'N/A'} ({d.address}) ...")

    try:
        async with BleakClient(d.address) as client:
            if client.is_connected:
                print(f"✅ Connected to {d.name or 'N/A'} ({d.address})")
                print("🔎 Discovering services ...")
                await client.get_services()
                for service in client.services:
                    print(f"[Service] {service.uuid}")
                    for char in service.characteristics:
                        print(f"  [Characteristic] {char.uuid} (props: {char.properties})")
                print("🔌 Disconnecting ...")
            else:
                print("❌ Connection failed.")
    except Exception as e:
        print(f"⚠️ Connection error: {e}")