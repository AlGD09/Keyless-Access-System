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
CHAR_RESPONSE = "0000aaa1-0000-1000-8001-aabbccddeeff"

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

            # Services abrufen
            await client.get_services()

            # Prüfen, ob Service existiert
            if SERVICE_UUID not in [s.uuid for s in client.services]:
                print("⚠️ Gesuchter Service nicht gefunden.")
                return False

            # Zufällige Challenge erzeugen
            challenge = os.urandom(16)
            print(f"🎲 Challenge erzeugt: {challenge.hex()}")

            # Challenge an Smartphone senden
            await client.write_gatt_char(CHAR_CHALLENGE, challenge)
            print("📤 Challenge an Smartphone gesendet.")

            # Kurz warten, damit das Smartphone antworten kann
            await asyncio.sleep(5.0)

            # Response auslesen
            response = await client.read_gatt_char(CHAR_RESPONSE)

            # --- NEU: Darstellung des Responses in Hex und Text ---
            hex_value = response.hex()
            try:
                text_value = response.decode("utf-8")
            except UnicodeDecodeError:
                text_value = "<nicht lesbarer Text>"

            print(f"📥 Response empfangen (HEX): {hex_value}")
            print(f"💬 Response als Text: {text_value}")

            # Tokenprüfung
            if response.endswith(EXPECTED_TOKEN):
                print("✅ Tokenprüfung erfolgreich – Authentifizierung bestanden.")
                return True
            else:
                print("❌ Tokenprüfung fehlgeschlagen.")
                return False

    except Exception as e:
        print(f"⚠️ Fehler bei Challenge-Response: {e}")
        return False
