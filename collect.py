import asyncio
import struct
import numpy as np
import csv
import os
import atexit
import sys
import keyboard
from datetime import datetime
from bleak import BleakClient

# 设备 MAC 地址（请替换为你的设备地址）
HRV_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"

# 心率测量服务和特性 UUID
HRV_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"  # 心率数据

# 存储所有采集数据
all_data = []

# 定义阶段，最多支持 10 个阶段
STAGE_LABELS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
stage_index = 0  # 当前阶段索引
stage_start_index = 0  # 记录当前阶段起始数据在 all_data 中的索引


#  计算 HRV
def calculate_rmssd(rr_intervals):
    if len(rr_intervals) < 2:
        return None
    diff_rr = np.diff(rr_intervals)
    squared_diffs = np.square(diff_rr)
    return round(float(np.sqrt(np.mean(squared_diffs))), 2)


def parse_hrv_data(data):
    """解析 BLE 设备数据"""
    data = bytearray(data)
    flags = data[0]

    # 解析心率
    hr = data[1]
    index = 2

    # 解析 R-R 间隔
    rr_intervals = []
    while index + 2 <= len(data):
        rr = struct.unpack("<H", data[index:index + 2])[0]
        rr_intervals.append(rr)
        index += 2

    return hr, rr_intervals


#  处理 HRV 数据
rr_interval_cache = []  # 用于计算 RMSSD


def on_hrv_data(sender, data):
    global all_data, rr_interval_cache

    hr, rr_intervals = parse_hrv_data(data)
    rr_interval_cache.extend(rr_intervals)

    # 只保留最近 60 条 R-R 数据计算 RMSSD
    if len(rr_interval_cache) > 60:
        rr_interval_cache = rr_interval_cache[-60:]

    rmssd = calculate_rmssd(rr_interval_cache)
    current_time = datetime.now().strftime("%H:%M:%S")

    # 记录数据
    all_data.append({
        "time": current_time,
        "hr": hr,
        "rr": rr_intervals,
        "rmssd": rmssd,
        "stage": STAGE_LABELS[stage_index]  # 记录当前阶段
    })

    print(f"{current_time} | 阶段: {STAGE_LABELS[stage_index]} | 心率: {hr} bpm | R-R: {rr_intervals} | RMSSD: {rmssd}")


#  保存 CSV

def export_stage_data(stage_label, start_idx, end_idx):
    """导出阶段性数据"""
    if end_idx <= start_idx:
        print(f"⚠️ 阶段 '{stage_label}' 没有新数据")
        return

    now_str = datetime.now().strftime("%m-%d_%H-%M")
    filename = f"subject_{now_str}_{stage_label}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["时间", "阶段", "心率 (bpm)", "R-R 间隔 (ms)", "HRV (RMSSD) (ms)"])
        for row in all_data[start_idx:end_idx]:
            writer.writerow([row["time"], row["stage"], row["hr"], row["rr"], row["rmssd"]])

    print(f"✅ 阶段 '{stage_label}' 数据已保存: {filepath}")


#  监听按键

def handle_key_press(e):
    """键盘事件处理函数"""
    global stage_index, stage_start_index

    # 只响应空格键按下事件(不响应释放事件)
    if e.event_type == keyboard.KEY_DOWN and e.name == "space":
        if stage_index < len(STAGE_LABELS):
            current_label = STAGE_LABELS[stage_index]
            export_stage_data(current_label, stage_start_index, len(all_data))

            stage_index += 1
            if stage_index >= len(STAGE_LABELS):
                print("⚠️ 已达到最大阶段数，后续按键无效")
            else:
                print(f"➡️ 进入下一个阶段: {STAGE_LABELS[stage_index]}")

            stage_start_index = len(all_data)


#  退出时保存

last_stage_saved = False


def save_last_stage():
    """程序终止时保存最后阶段"""
    global last_stage_saved, stage_index, stage_start_index
    if last_stage_saved:
        return

    label = STAGE_LABELS[stage_index] if stage_index < len(STAGE_LABELS) else STAGE_LABELS[-1]
    export_stage_data(label, stage_start_index, len(all_data))
    last_stage_saved = True


atexit.register(save_last_stage)


#  采集 BLE 数据

async def read_hrv():
    async with BleakClient(HRV_DEVICE_ADDRESS) as client:
        if not client.is_connected:
            print("❌ 无法连接到设备")
            return

        print("✅ 连接成功，订阅 HRV 数据...")
        await client.start_notify(HRV_CHARACTERISTIC_UUID, on_hrv_data)

        # 无限循环，只监听 BLE 数据
        while True:
            # 不再需要检测按键，改为使用callback
            await asyncio.sleep(0.2)  # 避免 CPU 过载


# 运行程序
def main():
    try:
        print("按空格键切换阶段，Ctrl+C 退出程序")

        # 只为空格键注册键盘钩子
        keyboard.on_press_key("space", handle_key_press, suppress=True)

        asyncio.run(read_hrv())
    except KeyboardInterrupt:
        print("\n手动退出程序...")
    finally:
        keyboard.unhook_all()  # 移除所有键盘钩子


if __name__ == "__main__":
    main()