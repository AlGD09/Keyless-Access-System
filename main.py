#!/usr/bin/env python3
# main.py – zentrale Steuerung

import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast import BusType
from ble.advertising import start_advertising
from ble.gatt_service import start_gatt_service

async def main():
    print("Starte BLE-System der RCU...")
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    ad_manager, ad_path = await start_advertising(bus)
    # await start_gatt_service(bus)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Beende BLE-System")
        await ad_manager.call_unregister_advertisement(ad_path, {})

if __name__ == "__main__":
    asyncio.run(main())
