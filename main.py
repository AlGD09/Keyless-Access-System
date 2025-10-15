#!/usr/bin/env python3
# main.py – BLE Advertising mit kurzer Nachricht

import asyncio
import os
from dbus_fast import BusType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method

class Advertisement(ServiceInterface):
    def __init__(self, bus, path):
        super().__init__('org.bluez.LEAdvertisement1')
        self.path = path
        self.props = {
            'Type': Variant('s', 'peripheral'),
            'LocalName': Variant('s', 'RCU_Test'),
            'ServiceData': Variant('a{sv}', {
                '9999': Variant('ay', b'Hallo')  # kurze Nachricht im ServiceData-Feld
            }),
            'IncludeTxPower': Variant('b', True),
        }

    def get_path(self):
        return self.path

    @method()
    def Release(self):
        print("Advertisement released")

async def main():
    os.system("bluetoothctl power on")
    os.system("bluetoothctl system-alias RCU_Test")
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    ad_manager = await bus.introspect('org.bluez', '/org/bluez/hci0')
    ad_manager_obj = bus.get_proxy_object('org.bluez', '/org/bluez/hci0', ad_manager)
    ad_manager_iface = ad_manager_obj.get_interface('org.bluez.LEAdvertisingManager1')

    ad = Advertisement(bus, '/org/bluez/example/advertisement0')
    bus.export('/org/bluez/example/advertisement0', ad)

    await ad_manager_iface.call_register_advertisement('/org/bluez/example/advertisement0', {})
    print("🔵 Advertising gestartet mit Nachricht 'Hallo' (Name: RCU_Test)")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await ad_manager_iface.call_unregister_advertisement('/org/bluez/example/advertisement0')
        print("🛑 Advertising beendet")

if __name__ == "__main__":
    asyncio.run(main())
