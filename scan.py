from bleak import BleakScanner
import asyncio

async def scan_devices():
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

asyncio.run(scan_devices())
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            