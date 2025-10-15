#!/usr/bin/env python3
# main.py - BLE Advertising über BlueZ-DBus (RCU-kompatibel)

import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, PropertyAccess
from dbus_fast import Variant

ADAPTER_IFACE = 'org.bluez.Adapter1'
LE_ADV_MGR_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADV_IFACE = 'org.bluez.LEAdvertisement1'
BLUEZ_SERVICE_NAME = 'org.bluez'
ADVERT_PATH = '/org/bluez/example/advertisement0'


class Advertisement(ServiceInterface):
    def __init__(self, bus, path):
        super().__init__(LE_ADV_IFACE)
        self.path = path
        self.bus = bus
        self.properties = {
            "Type": Variant("s", "peripheral"),
            "LocalName": Variant("s", "RCU_Test"),
            "Discoverable": Variant("b", True),
            "Includes": Variant("as", ["tx-power"]),
        }

    @method()
    def Release(self):
        print("Advertisement released")

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> 's':
        return self.properties["Type"].value


async def main():
    bus = await MessageBus().connect()

    obj = await bus.introspect(BLUEZ_SERVICE_NAME, "/org/bluez/hci0")
    adapter = bus.get_proxy_object(BLUEZ_SERVICE_NAME, "/org/bluez/hci0", obj)
    adv_manager = adapter.get_interface(LE_ADV_MGR_IFACE)

    advertisement = Advertisement(bus, ADVERT_PATH)
    bus.export(ADVERT_PATH, advertisement)

    try:
        await adv_manager.call_register_advertisement(ADVERT_PATH, {})
        print("Advertising gestartet als 'RCU_Test' ... Stop mit Ctrl+C")
        while True:
            await asyncio.sleep(2)
    except Exception as e:
        print("Fehler:", e)
    finally:
        try:
            await adv_manager.call_unregister_advertisement(ADVERT_PATH)
        except Exception:
            pass
        print("Advertising gestoppt")


if __name__ == "__main__":
    asyncio.run(main())
