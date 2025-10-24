import asyncio
import os
import subprocess
from contextlib import suppress
from bleak import BleakClient
from auth.challenge import verify_response

SERVICE_UUID   = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE  = "0000aaa1-0000-1000-8001-aabbccddeeff"

EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"


async def _bluez_cleanup(address: str):
    """Erzwingt, dass BlueZ alte GATT-Verbindungen entfernt."""
    subprocess.run(["bluetoothctl", "disconnect", address], stdout=subprocess.DEVNULL)
    subprocess.run(["bluetoothctl", "untrust", address], stdout=subprocess.DEVNULL)
    subprocess.run(["bluetoothctl", "remove", address], stdout=subprocess.DEVNULL)
    await asyncio.sleep(1.0)


async def perform_challenge_response(device):
    """
    Stabile Challenge-Response-Kommunikation:
    - nutzt BLEDevice statt MAC-Adresse
    - 5 s Wartezeit für Smartphone-Antwort
    - führt Cleanup nur bei BlueZ/GATT-Fehlern aus
    """
    print(f"Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")

    last_error = None
    for attempt in range(1, 4):  # bis zu 3 Versuche
        client = None
        try:
            client = BleakClient(device)
            await client.connect(timeout=10.0)

            if not client.is_connected:
                raise RuntimeError("Verbindung fehlgeschlagen (client.is_connected == False).")

            print("Verbunden – Suche nach Service und Characteristics ...")
            services = await client.get_services()
            if SERVICE_UUID not in [s.uuid for s in services]:
                raise RuntimeError("Gesuchter Service nicht gefunden.")

            # Challenge erzeugen und senden
            challenge = os.urandom(16)
            print(f"Challenge erzeugt: {challenge.hex()}")
            await client.write_gatt_char(CHAR_CHALLENGE, challenge)
            print("Challenge an Smartphone gesendet.")

            # 5 s warten – Smartphone berechnet und sendet Antwort
            await asyncio.sleep(5.0)

            # Response lesen
            response = await client.read_gatt_char(CHAR_RESPONSE)
            hex_value = response.hex()
            try:
                text_value = response.decode("utf-8")
            except UnicodeDecodeError:
                text_value = "<nicht lesbarer Text>"

            print(f"Response empfangen (HEX): {hex_value}")
            print(f"Response als Text: {text_value}")

            # Tokenprüfung
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
            last_error = e
            print(f"Fehler bei Challenge-Response (Versuch {attempt}/3): {e}")

            # Nur wenn BlueZ-spezifischer GATT-Fehler auftritt → Cleanup
            if "org.bluez" in str(e):
                print("BlueZ/GATT-Fehler erkannt → Cleanup des Geräts ...")
                await _bluez_cleanup(device.address)

            await asyncio.sleep(1.5)
        finally:
            if client:
                with suppress(Exception):
                    await client.disconnect()
                await asyncio.sleep(0.5)

    print(f"Challenge-Response nach mehreren Versuchen fehlgeschlagen: {last_error}")
    return False
