# unlocked/distance_check.py

import threading
import asyncio
from dbus_fast import BusType, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, PropertyAccess
from config import RCU_ID

BLUEZ_SERVICE_NAME = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"
AD_MANAGER_IF = "org.bluez.LEAdvertisingManager1"


# -------------------------------------------------------------------
#   Advertisement Object
# -------------------------------------------------------------------

class RcuAdvertisement(ServiceInterface):
    def __init__(self, rcu_id: str):
        super().__init__("org.bluez.LEAdvertisement1")

        self.ad_type = "broadcast"
        self.local_name = f"Maschine_{rcu_id}"

        payload = rcu_id.encode("utf-8")
        self.manufacturer_data = {
            0xFFFF: Variant("ay", payload)
        }

        self.service_uuids = ["0000aaa0-0000-1000-8000-aabbccddeeff"]

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
        print("[RCU-ADV] Advertisement released")


# -------------------------------------------------------------------
#   ASYNC Advertising functions (unchanged)
# -------------------------------------------------------------------

async def start_rcu_advertising():
    print(f"[RCU-ADV] Starte Advertising für RCU={RCU_ID}")

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    advertisement = RcuAdvertisement(RCU_ID)
    path = f"/org/bluez/rcu_advertisement_{RCU_ID}"

    bus.export(path, advertisement)

    intro = await bus.introspect(BLUEZ_SERVICE_NAME, ADAPTER_PATH)
    obj = bus.get_proxy_object(BLUEZ_SERVICE_NAME, ADAPTER_PATH, intro)

    ad_manager = obj.get_interface(AD_MANAGER_IF)
    await ad_manager.call_register_advertisement(path, {})

    print("[RCU-ADV] Advertising läuft")

    return bus, ad_manager, path


async def stop_rcu_advertising(bus, ad_manager, path):
    print("[RCU-ADV] Stoppe Advertising…")

    try:
        await ad_manager.call_unregister_advertisement(path)
    except Exception as e:
        print(f"[RCU-ADV] Fehler beim Unregister: {e}")

    bus.unexport(path)
    print("[RCU-ADV] Advertising gestoppt.")


# -------------------------------------------------------------------
#   THREAD WRAPPERS (solution)
# -------------------------------------------------------------------

def start_advertising_thread():
    
    loop = asyncio.new_event_loop()
    container = {}

    def runner():
        asyncio.set_event_loop(loop)
        bus, ad_manager, path = loop.run_until_complete(start_rcu_advertising())
        container["bus"] = bus
        container["ad_manager"] = ad_manager
        container["path"] = path
        loop.run_forever()    

    t = threading.Thread(target=runner, daemon=True)
    t.start()

    return container, loop


def stop_advertising_thread(container, loop):
    
    future = asyncio.run_coroutine_threadsafe(
        stop_rcu_advertising(
            container["bus"],
            container["ad_manager"],
            container["path"]
        ),
        loop
    )
    future.result()

    loop.stop()
