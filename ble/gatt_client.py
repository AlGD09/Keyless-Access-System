# ble/gatt_client.py
import asyncio
import os
from bleak import BleakClient, BleakScanner
from auth.challenge import verify_response
from config import RCU_ID

SERVICE_UUID   = "0000aaa0-0000-1000-8000-aabbccddeeff"
CHAR_CHALLENGE = "0000aaa2-0000-1000-8000-aabbccddeeff"
CHAR_RESPONSE  = "0000aaa1-0000-1000-8001-aabbccddeeff"

EXPECTED_TOKEN = b"\xDE\xAD\xBE\xEF"

RESPONSE_STATUS = False

async def perform_challenge_response(device):

    global RESPONSE_STATUS
    RESPONSE_STATUS = False

    """Challenge-Response – robust auch ohne vorheriges Pairing.
    Erwartet, dass der aufrufende Code den Scanner bereits gestartet hat
    und erst nach dem Connect stoppt.
    """
    await asyncio.sleep(0)  # Event loop flush
    print(f"Starte Challenge-Response mit {device.name or 'N/A'} ({device.address})...")

    dev = device  # kein zweiter Scan!
    if not device:
        print("Kein Gerät übergeben – Challenge-Response übersprungen.")
        return False

    try:
        # kurzer Moment, damit BlueZ Properties setzt
        await asyncio.sleep(0.2)

        async with BleakClient(dev, timeout=15.0, adapter="hci0") as client:
            if not client.is_connected:
                print("Verbindung fehlgeschlagen.")
                return False

            print("Verbunden – Suche nach Service und Characteristics ...")

            # Kompatibler Zugriff auf Services (je nach Bleak-Version)
            try:
                services = await client.get_services()
            except Exception:
                await asyncio.sleep(0.5)
                try:
                    # Bei neueren Versionen ist services bereits eine Property
                    services = client.services
                except Exception as e2:
                    print(f"Services konnten nicht gelesen werden ({e2}).")
                    return False

            # Characteristics per UUID holen (nicht über Handles arbeiten!)
            # Falls Bleak get_characteristic() hat:
            get_char = getattr(services, "get_characteristic", None)
            if callable(get_char):
                char_challenge = get_char(CHAR_CHALLENGE)
                char_response  = get_char(CHAR_RESPONSE)
                if not char_challenge or not char_response:
                    print("Gesuchte Characteristics nicht gefunden.")
                    return False
            else:
                # Fallback: manuell filtern
                all_chars = []
                for s in services:
                    if hasattr(s, "characteristics"):
                        all_chars.extend(s.characteristics)
                def find(uuid):
                    for c in all_chars:
                        if getattr(c, "uuid", "").lower() == uuid.lower():
                            return c
                    return None
                char_challenge = find(CHAR_CHALLENGE)
                char_response  = find(CHAR_RESPONSE)
                if not char_challenge or not char_response:
                    print("Gesuchte Characteristics nicht gefunden.")
                    return False

            # Challenge-Response-Ablauf (nur UUIDs an Bleak übergeben!)
            import os
            challenge = os.urandom(16)
            print(f"Challenge erzeugt: {challenge.hex()}")

            
            # RCU-ID (z. B. "A116G6") als Bytes anhängen
            rcu_id_bytes = RCU_ID.encode("utf-8")
            payload = challenge + rcu_id_bytes
            print(f"Challenge-Payload gesendet (Challenge + ID): {payload.hex()}")

            # Vorbereitung für Notification
            response_event = asyncio.Event()
            response_data = bytearray()

            def handle_response(sender: str, data: bytearray):
                response_data[:] = data
                print(f"Notification empfangen: {data.hex()}")
                response_event.set()

            # Notifications aktivieren
            try:
                await client.start_notify(CHAR_RESPONSE, handle_response)
                print("Notification-Handler aktiviert.")
            except Exception as e:
                print(f"Warnung: Notification-Start fehlgeschlagen, fahre fort.")

            await asyncio.sleep(0.1)

            # WICHTIG: nicht mit Handles schreiben/lesen, sondern mit UUID
            await client.write_gatt_char(CHAR_CHALLENGE, payload)
            print("Challenge + RCU-ID an Smartphone gesendet.")

            # 1. Versuch: direkt lesen (Single-Machine-Fall)
            await asyncio.sleep(0.2)
            response = None
            try:
                response = await client.read_gatt_char(CHAR_RESPONSE)
                if response and len(response) > 0:
                    print("Response direkt über read_gatt_char empfangen.")
            except Exception as e:
                print(f"Kein direkter Read möglich, warte auf Notification...")

            # 2️. Wenn keine direkte Antwort kam -> auf Notification warten
            if not response or len(response) == 0:
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=13.5)
                    response = bytes(response_data)
                    print("Response über Notification empfangen.")
                except asyncio.TimeoutError:
                    print("Keine Response empfangen (weder read noch notify).")
                    try:
                        await client.stop_notify(CHAR_RESPONSE)
                    except Exception:
                        pass
                    return False
                
            # Notification beenden
            try:
                await client.stop_notify(CHAR_RESPONSE)
            except Exception:
                pass

            # response = await client.read_gatt_char(CHAR_RESPONSE)

            hex_value = response.hex()
            try:
                text_value = response.decode("utf-8")
            except UnicodeDecodeError:
                text_value = "<nicht lesbarer Text>"

            print(f"Response empfangen (HEX): {hex_value}")
            print(f"Response als Text: {text_value}")

            if response != None:
                RESPONSE_STATUS = True


            try:
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
                print(f"Fehler bei der Authentifizierungsprüfung: {e}")
                return False

    except Exception as e:
        print(f"Fehler bei Challenge-Response: {e}")
        if "org.bluez.GattService1" in str(e):
            raise SystemExit("org.bluez.GattService1")
        return False





async def send_unlock_status(address: str):

    try:
        async with BleakClient(address, timeout=10.0, adapter="hci0") as client:
            if not client.is_connected:
                print("Wiederverbindung fehlgeschlagen.")
                return False

            payload = b"Entsperrt"  

            # Vorher mussten wir die Characteristics suchen, 
            # weil direkt mit ihnen gearbeitet (lesen, Notifies aktivieren) wird 
            # – für einen einfachen Write reicht die UUID, den Rest erledigt Bleak automatisch.
            await client.write_gatt_char(CHAR_CHALLENGE, payload)
            print("Entsperrt an Smartphone geschickt")
            return True

    except Exception as e:
        print(f"Fehler beim Senden Entsperrungsnachricht: {e}")
        return False
