#!/usr/bin/env python3
# main.py – BLE Advertising Test mit Name und Nachricht

import asyncio
import os
from dbus_fast import BusType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, PropertyAccess



BLUEZ_SERVICE_NAME = "org.bluez"
ADAPTER_OBJECT_PATH = "/org/bluez/hci0"
ADVERTISING_MANAGER_INTERFACE = "org.bluez.LEAdvertisingManager1"
ADVERTISING_OBJECT_PATH = "/org/bluez/example/advertisement0"

class Advertisement(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.LEAdvertisement1")
        self.ad_type = "peripheral"
        self.local_name = "RCU_Test"
        self.manufacturer_data = {0xFFFF: [72, 97, 108, 108, 111]}  # "Hallo" in ASCII
        self.service_uuids = []

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":
        return self.ad_type

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> "s":
        return self.local_name

    @dbus_property(access=PropertyAccess.READ)
    def ManufacturerData(self) -> "a{qv}":
        return self.manufacturer_data

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":
        return self.service_uuids

    @method()
    def Release(self):
        print("Advertisement released")

async def main():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    adv = Advertisement()
    bus.export(ADVERTISING_OBJECT_PATH, adv)

    introspection = await bus.introspect(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH)
    obj = bus.get_proxy_object(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH, introspection)
    ad_manager = obj.get_interface(ADVERTISING_MANAGER_INTERFACE)

    await ad_manager.call_register_advertisement(ADVERTISING_OBJECT_PATH, {})
    print("✅ Advertising gestartet als 'RCU_Test' mit Nachricht 'Hallo'")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await ad_manager.call_unregister_advertisement(ADVERTISING_OBJECT_PATH)
        print("🛑 Advertising gestoppt")

if __name__ == "__main__":
    asyncio.run(main())
