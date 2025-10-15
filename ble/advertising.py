#!/usr/bin/env python3
# ble/advertising.py – BLE Advertising mit Name und Nachricht

import asyncio
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
        self.manufacturer_data = {0xFFFF: Variant('ay', b'Hallo')}  # "Hallo"
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

async def start_advertising(bus):
    """Startet das BLE-Advertising über BlueZ"""
    adv = Advertisement()
    bus.export(ADVERTISING_OBJECT_PATH, adv)

    introspection = await bus.introspect(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH)
    obj = bus.get_proxy_object(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH, introspection)
    ad_manager = obj.get_interface(ADVERTISING_MANAGER_INTERFACE)

    await ad_manager.call_register_advertisement(ADVERTISING_OBJECT_PATH, {})
    print("✅ Advertising gestartet als 'RCU_Test' mit Nachricht 'Hallo'")

    return ad_manager, ADVERTISING_OBJECT_PATH
