# ble/gatt_service.py
import asyncio
from dbus_fast import BusType
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, PropertyAccess

BLUEZ_SERVICE_NAME = "org.bluez"
ADAPTER_OBJECT_PATH = "/org/bluez/hci0"
GATT_MANAGER_INTERFACE = "org.bluez.GattManager1"
APPLICATION_OBJECT_PATH = "/org/bluez/example/app"
SERVICE_PATH = "/org/bluez/example/service0"
CHAR_CHALLENGE_PATH = "/org/bluez/example/service0/char0"
CHAR_RESPONSE_PATH = "/org/bluez/example/service0/char1"

class ChallengeCharacteristic(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.GattCharacteristic1")
        self.uuid = "12345678-1234-5678-1234-56789abcdef1"
        self.value = bytearray(b"Hallo")

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return ["read"]

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":
        print("📡 ChallengeCharacteristic wurde gelesen.")
        return list(self.value)

class ResponseCharacteristic(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.GattCharacteristic1")
        self.uuid = "12345678-1234-5678-1234-56789abcdef2"
        self.value = bytearray()

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return ["write"]

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}"):
        self.value = bytearray(value)
        print(f"✏️  ResponseCharacteristic geschrieben: {self.value.decode(errors='ignore')}")

class RCUService(ServiceInterface):
    def __init__(self):
        super().__init__("org.bluez.GattService1")
        self.uuid = "12345678-1234-5678-1234-56789abcdef0"
        self.primary = True

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":
        return self.primary

async def start_gatt_service(bus):
    introspection = await bus.introspect(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH)
    obj = bus.get_proxy_object(BLUEZ_SERVICE_NAME, ADAPTER_OBJECT_PATH, introspection)
    gatt_manager = obj.get_interface(GATT_MANAGER_INTERFACE)

    service = RCUService()
    char_challenge = ChallengeCharacteristic()
    char_response = ResponseCharacteristic()

    bus.export(SERVICE_PATH, service)
    bus.export(CHAR_CHALLENGE_PATH, char_challenge)
    bus.export(CHAR_RESPONSE_PATH, char_response)

    await gatt_manager.call_register_application("/org/bluez/example/app", {})
    print("✅ GATT Service registriert (Challenge + Response verfügbar)")

    return gatt_manager
