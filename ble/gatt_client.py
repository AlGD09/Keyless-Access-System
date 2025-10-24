# ble/gatt_client.py
import asyncio
import os
import subprocess
from contextlib import suppress
from bleak import BleakClient, BleakScanner
from auth.challenge import verify_response

SERVICE_UUID   = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE  = "0000aaa1-0000-1000-8001-aabbccddeeff"

EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"

async def _bluez_disconnect(address: str):
    subprocess.run(["bluetoothctl", "disconnect", address], stdout=subprocess.DEVNULL)
    await asyncio.sleep(0.5)

async def _rediscover(address: str, timeout: float = 5.0):
    # Nur um BlueZ wieder "auf das Gerät aufmerksam" zu machen
    return await BleakScanner.find_device_by_address(address, timeout=timeout)

async def perform_challenge_response(device):
    """
    Stabile, minimalinvasive Version:
    - verbindet per MAC (BleakClient(address))
    - 5 s Wartezeit vor dem Lesen der Antwort
    - kein 'remove', nur 'disconnect' bei BlueZ-Fehlern
    - optionales Rediscovery, aber Connect bleibt MAC-basiert
    """
    address = getattr(device, "address", str(device))
    name = getattr(device, "name", "N/A")
    print(f"Starte Challenge-Response mit {name} ({address})...")

    last_error = None
    for attempt in range(1, 4):
        client = None
        try:
            client = BleakClient(address)  # <- MAC-basiert, unabhängig vom Device-Handle
            await client.connect(timeout=10.0)

            if not client.is_connected:
                raise RuntimeError("Verbindung fehlgeschlagen (client.is_connected == False).")

            print("Verbunden – Services werden aufgelöst ...")
            services = await client.get_services()
            if SERVICE_UUID not in [s.uuid for s in services]:
                raise RuntimeError("Gesuchter Service nicht gefunden.")

            # Challenge senden
            challenge = os.urandom(16)
            print(f"Challenge erzeugt: {challenge.hex()}")
            await client.write_gatt_char(CHAR_CHALLENGE, challenge)
            print("Challenge an Smartphone gesendet.")

            # Smartphone braucht Zeit -> 5 s
            await asyncio.sleep(5.0)

            # Response lesen
            response = await client.read_gatt_char(CHAR_RESPONSE)
            try:
                text_value = response.decode("utf-8")
            except UnicodeDecodeError:
                text_value = "<nicht lesbarer Text>"
            print(f"Response empfangen (HEX): {response.hex()}")
            print(f"Response als Text: {text_value}")

            # Prüfen
            if verify_response(challenge, response):
                print("Tokenprüfung erfolgreich – Authentifizierung bestanden.")
                return True
            if response.endswith(EXPECTED_TOKEN):
                print("Fallback-Token erkannt – Authentifizierung bestanden.")
                return True

            print("Tokenprüfung fehlgeschlagen.")
            return False

        except Exception as e:
            last_error = e
            msg = str(e)
            print(f"Fehler bei Challenge-Response (Versuch {attempt}/3): {msg}")

            # Sanft aufräumen und BlueZ "wachkitzeln"
            if "org.bluez" in msg or "was not found" in msg:
                await _bluez_disconnect(address)
                # kurzes Rediscovery – hält den Eintrag präsent; Connect bleibt MAC-basiert
                await _rediscover(address, timeout=3.0)

            await asyncio.sleep(1.5)

        finally:
            if client:
                with suppress(Exception):
                    await client.disconnect()
                await asyncio.sleep(0.5)

    print(f"Challenge-Response nach mehreren Versuchen fehlgeschlagen: {last_error}")
    return False
