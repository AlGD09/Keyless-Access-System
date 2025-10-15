#!/usr/bin/env python3
# main.py – Testprogramm für RCU-Funktionalität

from bleak import BleakAdvertiser
import asyncio

async def main():
    async with BleakAdvertiser(advertisement_data={"local_name": "RCU_Test"}) as adv:
        print("Advertising as RCU_Test... Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())


