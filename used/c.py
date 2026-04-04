import asyncio
import struct
import numpy as np
import csv
import os
import atexit
from datetime import datetime
from bleak import BleakClient

# 设备 MAC 地址
HRV_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"

# 心率测量服务和特性 UUID
HRV_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"  # 心率数据

# 缓存数据
rr_interval_cache = []  # R-R 间隔
hr_cache = []  # 记录心率数据
rmssd_cache = []  # 记录 HRV (RMSSD)
timestamps = []  # 记录时间戳


# 计算 HRV (RMSSD)
def calculate_rmssd(rr_intervals):
    if len(rr_intervals) < 2:
        return None  # 需要至少两个 R-R 间隔
    diff_rr = np.diff(rr_intervals)  # 计算相邻 R-R 间隔的差值
    squared_diffs = np.square(diff_rr)  # 平方
    rmssd = np.sqrt(np.mean(squared_diffs))  # 均值的平方根
    return round(rmssd, 2)


# 解析 HRV 设备的数据
def parse_hrv_data(data):
    """解析 HRV 设备传来的 bytearray 数据"""
    data = bytearray(data)
    flags = data[0]

    # 解析心率
    if flags & 0x01 == 0:
        hr = data[1]  # 8-bit heart rate
        index = 2
    else:
        hr = struct.unpack("<H", data[1:3])[0]  # 16-bit heart rate
        index = 3

    # 解析 R-R 间隔（HRV 数据）
    rr_intervals = []
    while index + 2 <= len(data):
        rr = struct.unpack("<H", data[index:index + 2])[0]
        rr_intervals.append(rr)
        index += 2

    return hr, rr_intervals


# 接收 HRV 数据
async def notification_handler(sender, data):
    global rr_interval_cache, hr_cache, timestamps, rmssd_cache

    hr, rr_intervals = parse_hrv_data(data)

    # 记录数据
    rr_interval_cache.extend(rr_intervals)
    hr_cache.append(hr)
    timestamps.append(datetime.now().strftime("%H:%M:%S"))  # 记录时间

    # 保持最近 60 秒的数据
    if len(rr_interval_cache) > 60:
        rr_interval_cache = rr_interval_cache[-60:]
        hr_cache = hr_cache[-60:]
        timestamps = timestamps[-60:]

    # 计算 HRV (RMSSD)
    rmssd = calculate_rmssd(rr_interval_cache)
    rmssd_cache.append(rmssd)  # 记录 HRV 数据

    # 打印数据
    print(f" {timestamps[-1]} | 心率: {hr} bpm | R-R 间隔: {rr_intervals} ms | HRV (RMSSD): {rmssd} ms")


# 保存数据到 CSV
def save_data():
    """程序终止时自动保存数据"""
    if len(rr_interval_cache) == 0:
        print(" 没有数据可保存")
        return

    # 生成文件名：2-11_05-24.csv
    now = datetime.now().strftime("%m-%d_%H-%M")
    filename = f"HRV_{now}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    # 写入 CSV 文件
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["时间", "心率 (bpm)", "R-R 间隔 (ms)", "HRV (RMSSD) (ms)"])  # CSV 头部
        for i in range(len(hr_cache)):
            writer.writerow([timestamps[i], hr_cache[i], rr_interval_cache[i], rmssd_cache[i]])

    print(f"数据已保存至 {filepath}")


# 在程序终止时自动保存
atexit.register(save_data)


# 连接设备并监听数据
async def read_hrv():
    async with BleakClient(HRV_DEVICE_ADDRESS) as client:
        if not client.is_connected:
            print("无法连接到设备")
            return

        print("连接成功，订阅 HRV 数据...")
        await client.start_notify(HRV_CHARACTERISTIC_UUID, notification_handler)

        # 无限运行，持续接收数据
        while True:
            await asyncio.sleep(1)  # 每秒钟保持监听


# 运行程序
if __name__ == "__main__":
    asyncio.run(read_hrv())
