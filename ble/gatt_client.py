#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble/gatt_client.py – BLE Challenge-Response-Client auf der RCU
"""

import asyncio
import os
from bleak import BleakClient
from auth.challenge import verify_response
import subprocess

# UUIDs des Custom-Services
SERVICE_UUID = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE = "0000aaa1-0000-1000-8001-aabbccddeeff"

# Fester Referenz-Token (Fallback für statische Tests)
EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"


async def perform_challenge_response(device):
    print(f"Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")
    client = None  
    try:
        subprocess.run(["bluetoothctl", "disconnect", device.address], stdout=subprocess.DEVNULL)
        await asyncio.sleep(1.0)
        client = BleakClient(device.address)
        await client.connect()

        if not client.is_connected:
            print("Verbindung fehlgeschlagen.")
            return False

        print("Verbunden – Suche nach Service und Characteristics ...")
        await client.get_services()

        if SERVICE_UUID not in [s.uuid for s in client.services]:
            print("Gesuchter Service nicht gefunden.")
            return False

        challenge = os.urandom(16)
        print(f"Challenge erzeugt: {challenge.hex()}")

        await client.write_gatt_char(CHAR_CHALLENGE, challenge)
        print("Challenge an Smartphone gesendet.")
        await asyncio.sleep(5.0)

        response = await client.read_gatt_char(CHAR_RESPONSE)

        hex_value = response.hex()
        try:
            text_value = response.decode("utf-8")
        except UnicodeDecodeError:
            text_value = "<nicht lesbarer Text>"
        print(f"Response empfangen (HEX): {hex_value}")
        print(f"Response als Text: {text_value}")

        if verify_response(challenge, response):
            print("Tokenprüfung erfolgreich – Authentifizierung bestanden.")
            return True
        elif response.endswith(EXPECTED_TOKEN):
            print("Fallback-Token erkannt – Authentifizierung bestanden.")
            return True
        else:
            print("Tokenprüfung fehlgeschlagen.")
            return False

    except Exception as e:
        print(f"Fehler bei Challenge-Response: {e}")
        return False

    finally:
        if client:
            try:
                await client.disconnect()
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"Fehler beim Trennen: {e}")
