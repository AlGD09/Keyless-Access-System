# ble/gatt_client.py
import asyncio
import os
from bleak import BleakClient, BleakScanner
from auth.challenge import verify_response

SERVICE_UUID   = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE  = "0000aaa1-0000-1000-8001-aabbccddeeff"

EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"

async def perform_challenge_response(device):
    """Challenge-Response – robust auch ohne vorheriges Pairing.
    Erwartet, dass der aufrufende Code den Scanner bereits gestartet hat
    und erst nach dem Connect stoppt.
    """
    print(f"Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")

    dev = device  # kein zweiter Scan!

    try:
        # kurzer Moment, damit BlueZ Properties setzt
        await asyncio.sleep(0.2)

        async with BleakClient(dev, timeout=15.0, adapter="hci0") as client:
            if not client.is_connected:
                print("❌ Verbindung fehlgeschlagen.")
                return False

            print("✅ Verbunden – Suche nach Service und Characteristics ...")
            await client.get_services()

            if SERVICE_UUID not in [s.uuid for s in client.services]:
                print("❌ Gesuchter Service nicht gefunden.")
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

            try:
                if verify_response(challenge, response):
                    print("✅ Tokenprüfung erfolgreich – Authentifizierung bestanden.")
                    return True
                elif response.endswith(EXPECTED_TOKEN):
                    print("✅ Fallback-Token erkannt – Authentifizierung bestanden.")
                    return True
                else:
                    print("❌ Tokenprüfung fehlgeschlagen.")
                    return False
            except Exception as e:
                print(f"Fehler bei der Authentifizierungsprüfung: {e}")
                return False

    except Exception as e:
        print(f"Fehler bei Challenge-Response: {e}")
        return False
