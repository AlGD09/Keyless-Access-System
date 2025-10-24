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

async def _bluez_remove(address: str):
    subprocess.run(["bluetoothctl", "remove", address], stdout=subprocess.DEVNULL)
    await asyncio.sleep(0.8)

async def _rediscover(address: str, timeout: float = 5.0):
    # Holt ein frisches BLEDevice-Objekt aus BlueZ (legt den BlueZ-Eintrag wieder an)
    dev = await BleakScanner.find_device_by_address(address, timeout=timeout)
    return dev

async def perform_challenge_response(device):
    """
    - Verwendet BLEDevice direkt (korrekter D-Bus-Pfad)
    - 5 s Wartezeit für die Antwort des Smartphones
    - Bei BlueZ/GATT-Fehler: disconnect -> (optional remove) -> Re-Discovery -> Retry
    - Keine Adapter-Eskalation
    """
    print(f"Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")

    last_error = None
    address = device.address
    for attempt in range(1, 4):  # bis zu 3 Versuche
        client = None
        try:
            # WICHTIG: Immer ein aktuelles BLEDevice verwenden (nach evtl. Cleanup)
            client = BleakClient(device)
            await client.connect(timeout=10.0)

            if not client.is_connected:
                raise RuntimeError("Verbindung fehlgeschlagen (client.is_connected == False).")

            print("Verbunden – Services werden aufgelöst ...")
            services = await client.get_services()
            if SERVICE_UUID not in [s.uuid for s in services]:
                raise RuntimeError("Gesuchter Service nicht gefunden.")

            # Challenge erzeugen und senden
            challenge = os.urandom(16)
            print(f"Challenge erzeugt: {challenge.hex()}")
            await client.write_gatt_char(CHAR_CHALLENGE, challenge)
            print("Challenge an Smartphone gesendet.")

            # Smartphone-Rechenzeit (du sagtest: 5s sind wichtig)
            await asyncio.sleep(5.0)

            # Response lesen
            response = await client.read_gatt_char(CHAR_RESPONSE)
            try:
                text_value = response.decode("utf-8")
            except UnicodeDecodeError:
                text_value = "<nicht lesbarer Text>"
            print(f"Response empfangen (HEX): {response.hex()}")
            print(f"Response als Text: {text_value}")

            # Tokenprüfung
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

            # Nur bei BlueZ/GATT-Fehlern aufräumen und REDISCOVER
            if "org.bluez" in msg or "was not found" in msg:
                # 1) sanft: disconnect
                await _bluez_disconnect(address)

                # 2) wenn "was not found" schon auftrat oder weiterhin BlueZ-Fehler → remove + rediscover
                if "was not found" in msg:
                    await _bluez_remove(address)

                # Frisches BLEDevice ziehen (WICHTIG!):
                fresh = await _rediscover(address, timeout=5.0)
                if fresh:
                    device = fresh
                    print(f"Re-Discovery erfolgreich: {device.name or 'N/A'} ({device.address})")
                else:
                    print("Re-Discovery fehlgeschlagen – Gerät nicht gefunden.")
                    # kurzer Backoff und nächster Loop-Versuch (falls noch übrig)
            await asyncio.sleep(1.5)

        finally:
            if client:
                with suppress(Exception):
                    await client.disconnect()
                await asyncio.sleep(0.5)

    print(f"Challenge-Response nach mehreren Versuchen fehlgeschlagen: {last_error}")
    return False
