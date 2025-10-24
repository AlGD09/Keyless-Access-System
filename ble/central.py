#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/central.py – BLE Central-Logik der RCU (Modul)
Erkennt Geräte anhand ihrer Manufacturer Data (Company Identifier + Payload)
und liefert die Treffer an main.py zurück (main steuert Connect/Challenge).
"""

import asyncio
import contextlib
from bleak import BleakScanner, BleakClient

# ---------------------------------------------------------
# Zielparameter aus Cloud laden (Device-ID des Smartphones)
# ---------------------------------------------------------
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
    print(f"Scanning for BLE devices for {timeout} s ...")
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
                print("↪︎ 0xFFFF gesehen, aber keine Device-ID gesetzt → überspringe.")
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


async def find_target_device_keep_scanning(timeout: int = 10):
    """
    Startet einen Scan und liefert (device, scanner) zurück, sobald das Zielgerät
    gefunden wurde. Der Scanner bleibt AKTIV, bis der Aufrufer ihn stoppt.
    """
    print(f"Scanning for BLE devices for {timeout} s (Scanner bleibt aktiv) ...")
    scanner = BleakScanner(adapter="hci0")
    await scanner.start()

    selected = None
    try:
        end = asyncio.get_event_loop().time() + timeout
        printed = set()

        while asyncio.get_event_loop().time() < end and selected is None:
            await asyncio.sleep(0.4)
            for d in await scanner.get_discovered_devices():
                # Einmaliges Logging
                if d.address not in printed:
                    name = d.name or "N/A"
                    mdata = d.metadata.get("manufacturer_data", {})
                    if mdata:
                        for comp_id, payload in mdata.items():
                            try:
                                payload_hex = payload.hex()
                            except Exception:
                                payload_hex = str(payload)
                            print(f"📡 {name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload_hex}")
                    printed.add(d.address)

                # Matching
                mdata = d.metadata.get("manufacturer_data", {})
                if not mdata:
                    continue
                for comp_id, payload in mdata.items():
                    if comp_id != TARGET_MANUFACTURER_ID:
                        continue
                    if TARGET_DEVICE_BYTES is None:
                        continue
                    if TARGET_DEVICE_BYTES in payload:
                        print(f"✅ Matching device gefunden: {d.name or 'N/A'} ({d.address})")
                        selected = d
                        break
                if selected:
                    break

        if selected is None:
            await scanner.stop()
            return None, None

        # Scanner absichtlich NICHT stoppen – Aufrufer macht das später.
        return selected, scanner

    except Exception:
        with contextlib.suppress(Exception):
            await scanner.stop()
        raise
