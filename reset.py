import asyncio
from bleak import BleakClient, BleakScanner

TARGET_MAC = "A4:FC:77:5C:B3:90"

async def reconnect():
    print(f"Starte gezielten Reconnect mit {TARGET_MAC} ...")

    # Schritt 1: aktiven Scan starten (damit BlueZ das Device registriert)
    scanner = BleakScanner(adapter="hci0")
    await scanner.start()
    print("Scanning...")
    device = await BleakScanner.find_device_by_address(TARGET_MAC, timeout=15.0)
    await scanner.stop()

    if not device:
        print("❌ Gerät nicht gefunden – bitte einschalten und in Reichweite bringen.")
        return

    print(f"✅ Gerät gefunden: {device.name} ({device.address})")

    # Schritt 2: direkte Verbindung aufbauen
    try:
        async with BleakClient(device, adapter="hci0", timeout=15.0) as client:
            if client.is_connected:
                print("✅ Verbindung erfolgreich aufgebaut.")
                print("💾 Gerät wird nun wieder von BlueZ gespeichert.")
            else:
                print("❌ Verbindung fehlgeschlagen.")
    except Exception as e:
        print(f"Fehler beim Reconnect: {e}")

    # Schritt 3: Verbindung wieder trennen
    print("Vorgang abgeschlossen. Gerät sollte nun erneut in bluetoothctl sichtbar sein.")

asyncio.run(reconnect())
