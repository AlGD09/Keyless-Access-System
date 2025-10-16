#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/gatt_client.py – BLE Challenge-Response-Client auf der RCU
"""

import asyncio
import os
from bleak import BleakClient

# UUIDs des Custom-Services
SERVICE_UUID = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE = "0000aaa1-0000-1000-8000-aabbccddeeff"

# Fester Referenz-Token (z. B. symmetrischer Schlüssel für Testzwecke)
EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"


async def perform_challenge_response(device):
    """Führt den Challenge-Response-Austausch mit dem angegebenen Gerät durch."""
    print(f"🔗 Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")

    try:
        async with BleakClient(device.address) as client:
            if not client.is_connected:
                print("❌ Verbindung fehlgeschlagen.")
                return False

            print("✅ Verbunden – Suche nach Service und Characteristics ...")

            # Verfügbare Services abrufen
            await client.get_services()

            if SERVICE_UUID not in [s.uuid for s in client.services]:
                print("⚠️ Gesuchter Service nicht gefunden.")
                return False

            # Challenge erzeugen (16 Byte)
            challenge = os.urandom(16)
            print(f"🎲 Challenge erzeugt: {challenge.hex()}")

            # Challenge an das Smartphone senden
            await client.write_gatt_char(CHAR_CHALLENGE, challenge)
            print("📤 Challenge an Smartphone gesendet.")

            # Kurz warten, damit Smartphone Zeit hat zu antworten
            await asyncio.sleep(10.0)

            # Antwort lesen
            response = await client.read_gatt_char(CHAR_RESPONSE)
            print(f"📥 Response empfangen: {response.hex()}")

            # Token-Prüfung (Beispiel: Response muss mit EXPECTED_TOKEN enden)
            if response.endswith(EXPECTED_TOKEN):
                print("✅ Tokenprüfung erfolgreich – Authentifizierung bestanden.")
                return True
            else:
                print("❌ Tokenprüfung fehlgeschlagen.")
                return False

    except Exception as e:
        print(f"⚠️ Fehler bei Challenge-Response: {e}")
        return False
