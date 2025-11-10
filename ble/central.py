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
from typing import List

# ---------------------------------------------------------
# Zielparameter aus Cloud laden (Device-ID des Smartphones)
# ---------------------------------------------------------
TARGET_DEVICE_BYTES_LIST = []

# Gesuchter Manufacturer Identifier (16-bit Company ID)
TARGET_MANUFACTURER_ID = 0xFFFF



async def find_best_authorized_device(devices_authorized: List[bytes], timeout: int = 10):
    """
    Scannt BLE-Geräte über 'timeout' Sekunden und wählt das autorisierte Gerät
    mit dem höchsten RSSI aus.
    Rückgabe: (selected_device, matched_device_id_hex, scanner)
              oder (None, None, None) bei keinem Treffer.
    """
    print(f"[BLE] Scanning {timeout}s nach autorisierten Geräten ({len(devices_authorized)} known)...")
    scanner = BleakScanner(adapter="hci0")
    await scanner.start()

    authorized_hits = []  # (device, rssi, matched_bytes)
    printed = set()

    try:
        end_time = asyncio.get_event_loop().time() + timeout

        # Wenn nur ein autorisiertes Gerät übergeben wurde
        single_mode = len(devices_authorized) == 1
        if single_mode:
            print("[BLE] Nur ein autorisiertes Gerät vorhanden → Auswahl erfolgt beim ersten Treffer ohne RSSI-Vergleich.")


        while asyncio.get_event_loop().time() < end_time:
            await asyncio.sleep(0.4)

            for d in await scanner.get_discovered_devices():
                mdata = d.metadata.get("manufacturer_data", {})
                if not mdata:
                    continue

                # Einmaliges Logging aller gefundenen Geräte
                if d.address not in printed:
                    name = d.name or "N/A"
                    for comp_id, payload in mdata.items():
                        try:
                            payload_hex = payload.hex()
                        except Exception:
                            payload_hex = str(payload)
                        print(f"{name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload_hex}")
                    printed.add(d.address)

                # Matching autorisierter Devices
                for comp_id, payload in mdata.items():
                    if comp_id != TARGET_MANUFACTURER_ID:
                        continue
                    for target_bytes in devices_authorized:
                        if target_bytes in payload:
                            if single_mode:
                                matched_hex = target_bytes.hex()
                                print(f"[BLE] → Autorisiertes Gerät erkannt: {d.name or 'N/A'} "
                                      f"({d.address}) deviceId={matched_hex} (Single-Mode)")
                                return d, matched_hex, scanner  # Direkt zurückgeben
                            else:
                                authorized_hits.append((d, d.rssi, target_bytes))
                                print(f"[BLE] Autorisiertes Gerät erkannt: {d.name or 'N/A'} ({d.address}) RSSI={d.rssi}")
                            break

        if not authorized_hits:
            print("[BLE] Kein autorisiertes Gerät innerhalb des Zeitfensters gefunden.")
            await scanner.stop()
            return None, None, None

        # Gerät mit höchstem RSSI auswählen
        selected_device, best_rssi, matched_bytes = max(authorized_hits, key=lambda x: x[1])
        matched_hex = matched_bytes.hex()
        print(f"[BLE] → Ausgewählt: {selected_device.name or 'N/A'} "
              f"({selected_device.address}) mit RSSI={best_rssi} dBm "
              f"und deviceId={matched_hex}")

        # Scanner aktiv lassen (Challenge läuft danach)
        return selected_device, matched_hex, scanner

    except Exception as e:
        print(f"[BLE] Fehler beim Scan: {e}")
        with contextlib.suppress(Exception):
            await scanner.stop()
        raise







"""
async def find_target_device_keep_scanning(timeout: int = 10):
    
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
                            print(f"{name} ({d.address}) → CompanyID: 0x{comp_id:04X}, Data: {payload_hex}")
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
                        print(f"Matching device gefunden: {d.name or 'N/A'} ({d.address})")
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
"""