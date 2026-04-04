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
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import threading

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 固定蓝牙设备MAC地址
HRV_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"

# 心率测量服务和特性 UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"  # 心率服务
HRV_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"  # 心率数据

# 存储所有采集数据
all_data = []

# 为实时绘图准备数据队列
time_data = deque(maxlen=100)  # 最近100个时间点
hr_data = deque(maxlen=100)  # 最近100个心率值
rmssd_data = deque(maxlen=100)  # 最近100个RMSSD值
stage_markers = []  # 存储阶段变化的时间点

# 模拟数据模式（当无法连接到真实设备时使用）
SIMULATION_MODE = False
last_simulated_hr = 70  # 初始模拟心率值

# 定义阶段，最多支持 10 个阶段
STAGE_LABELS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
STAGE_COLORS = ['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'brown', 'black']
stage_index = 0  # 当前阶段索引
stage_start_index = 0  # 记录当前阶段起始数据在 all_data 中的索引

# 创建图形和子图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.canvas.manager.set_window_title('心率和HRV实时监测')
line1, = ax1.plot([], [], 'r-', linewidth=2, label='心率 (BPM)')
line2, = ax2.plot([], [], 'b-', linewidth=2, label='HRV (RMSSD)')

# 设置图表属性
ax1.set_title('实时心率监测')
ax1.set_xlabel('')
ax1.set_ylabel('心率 (BPM)')
ax1.grid(True)
ax1.legend(loc='upper right')

ax2.set_title('实时HRV监测')
ax2.set_xlabel('时间点')
ax2.set_ylabel('RMSSD (ms)')
ax2.grid(True)
ax2.legend(loc='upper right')


# 计算 HRV
def calculate_rmssd(rr_intervals):
    if len(rr_intervals) < 2:
        return None
    diff_rr = np.diff(rr_intervals)
    squared_diffs = np.square(diff_rr)
    return round(float(np.sqrt(np.mean(squared_diffs))), 2)


def parse_hrv_data(data):
    """解析 BLE 设备数据"""
    try:
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
    except Exception as e:
        print(f"解析心率数据失败: {e}")
        return 0, []


# 生成模拟心率数据（当无法连接到设备时使用）
def generate_simulated_data():
    global last_simulated_hr

    # 生成一个随机波动的心率
    variation = np.random.normal(0, 2)  # 随机波动，标准差为2
    last_simulated_hr = max(40, min(120, last_simulated_hr + variation))  # 限制在40-120范围内
    hr = int(last_simulated_hr)

    # 生成模拟的RR间隔
    # 心率为60bpm时，RR间隔约为1000ms
    base_rr = 60000 / hr
    rr_intervals = [int(base_rr + np.random.normal(0, 20)) for _ in range(np.random.randint(0, 3))]

    return hr, rr_intervals


# 处理 HRV 数据
rr_interval_cache = []  # 用于计算 RMSSD


def on_hrv_data(sender, data):
    global all_data, rr_interval_cache, time_data, hr_data, rmssd_data

    # 解析数据
    if SIMULATION_MODE:
        hr, rr_intervals = generate_simulated_data()
    else:
        hr, rr_intervals = parse_hrv_data(data)

    rr_interval_cache.extend(rr_intervals)

    # 只保留最近 60 条 R-R 数据计算 RMSSD
    if len(rr_interval_cache) > 60:
        rr_interval_cache = rr_interval_cache[-60:]

    rmssd = calculate_rmssd(rr_interval_cache)
    current_time = datetime.now().strftime("%H:%M:%S")

    # 添加数据到可视化队列
    time_data.append(current_time)
    hr_data.append(hr)
    if rmssd is not None:
        rmssd_data.append(rmssd)
    else:
        rmssd_data.append(0)  # 无有效RMSSD时填充0

    # 记录数据
    all_data.append({
        "time": current_time,
        "hr": hr,
        "rr": rr_intervals,
        "rmssd": rmssd,
        "stage": STAGE_LABELS[stage_index]  # 记录当前阶段
    })

    print(f"{current_time} | 阶段: {STAGE_LABELS[stage_index]} | 心率: {hr} bpm | R-R: {rr_intervals} | RMSSD: {rmssd}")


# 模拟数据发送（无设备连接时）
async def simulate_hrv_data():
    while True:
        # 模拟数据回调
        on_hrv_data(None, None)
        await asyncio.sleep(1)  # 每秒发送一次模拟数据


# 更新图表的函数
def update_plot(frame):
    if len(time_data) > 0:
        # 更新心率图
        x_range = list(range(len(time_data)))
        line1.set_data(x_range, list(hr_data))
        ax1.set_xlim(0, max(100, len(time_data)))
        y_min = max(40, min(hr_data) - 5) if hr_data else 40
        y_max = min(200, max(hr_data) + 5) if hr_data else 100
        ax1.set_ylim(y_min, y_max)

        # 更新HRV图
        line2.set_data(x_range, list(rmssd_data))
        ax2.set_xlim(0, max(100, len(time_data)))
        y_min_rmssd = max(0, min(rmssd_data) - 5) if rmssd_data else 0
        y_max_rmssd = min(200, max(rmssd_data) + 5) if rmssd_data else 50
        ax2.set_ylim(y_min_rmssd, y_max_rmssd)

        # 添加时间轴标签
        ax1.set_xticks(
            [0, len(time_data) // 4, len(time_data) // 2, 3 * len(time_data) // 4, len(time_data) - 1] if len(
                time_data) > 4 else range(len(time_data)))
        ax1.set_xlabel('')  # 移除上图的x轴标签
        ax2.set_xticks(
            [0, len(time_data) // 4, len(time_data) // 2, 3 * len(time_data) // 4, len(time_data) - 1] if len(
                time_data) > 4 else range(len(time_data)))

        # 绘制阶段分割线，但不添加标签
        for mark in stage_markers:
            if mark['index'] < len(time_data):
                ax1.axvline(x=mark['index'], color=mark['color'], linestyle='--', alpha=0.7)
                ax2.axvline(x=mark['index'], color=mark['color'], linestyle='--', alpha=0.7)
                # 已删除标签文本代码

    return line1, line2


# 保存 CSV
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


# 新的键盘事件处理函数
def handle_key_press(e):
    """键盘事件处理函数"""
    global stage_index, stage_start_index

    # 只响应空格键按下事件(不响应释放事件)
    if e.event_type == keyboard.KEY_DOWN and e.name == "space":
        if stage_index < len(STAGE_LABELS):
            current_label = STAGE_LABELS[stage_index]
            export_stage_data(current_label, stage_start_index, len(all_data))

            # 记录阶段变化点用于可视化
            if len(time_data) > 0:
                stage_markers.append({
                    'index': len(time_data) - 1,
                    'label': f'{current_label}结束',
                    'color': STAGE_COLORS[stage_index % len(STAGE_COLORS)]
                })

            stage_index += 1
            if stage_index >= len(STAGE_LABELS):
                print("⚠️ 已达到最大阶段数，后续按键无效")
            else:
                print(f"➡️ 进入下一个阶段: {STAGE_LABELS[stage_index]}")
                # 记录新阶段开始点
                if len(time_data) > 0:
                    stage_markers.append({
                        'index': len(time_data) - 1,
                        'label': f'{STAGE_LABELS[stage_index]}开始',
                        'color': STAGE_COLORS[stage_index % len(STAGE_COLORS)]
                    })

            stage_start_index = len(all_data)


# 退出时保存
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


# 启动可视化的线程
def start_visualization():
    try:
        ani = FuncAnimation(fig, update_plot, interval=500, blit=False)  # 更新间隔减少到500ms，提高响应性
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"可视化启动失败: {e}")
        plt.close(fig)  # 关闭图形以防止资源泄漏


# 采集 BLE 数据
async def read_hrv():
    global SIMULATION_MODE, HRV_DEVICE_ADDRESS

    print(f"将连接到设备: {HRV_DEVICE_ADDRESS}")

    try:
        print(f"尝试连接到设备: {HRV_DEVICE_ADDRESS}")

        # 创建客户端实例
        client = BleakClient(HRV_DEVICE_ADDRESS)

        # 尝试连接，增加超时时间，并添加额外的重试逻辑
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                print(f"连接尝试 {retry_count + 1}/{max_retries}...")
                connected = await asyncio.wait_for(client.connect(), timeout=15.0)

                if connected:
                    print("✅ 连接成功!")
                    break
                else:
                    print(f"连接失败，尝试重试...")
            except Exception as e:
                print(f"连接异常: {e}")

            retry_count += 1
            if retry_count < max_retries:
                print("等待2秒后重试...")
                await asyncio.sleep(2)

        if not client.is_connected:
            print("❌ 达到最大重试次数，无法连接到设备，将使用模拟数据")
            SIMULATION_MODE = True
            await simulate_hrv_data()
            return

        print("✅ 连接成功，订阅 HRV 数据...")

        try:
            await client.start_notify(HRV_CHARACTERISTIC_UUID, on_hrv_data)
            print("成功订阅心率数据特征值")
        except Exception as e:
            print(f"❌ 无法订阅心率数据特征值: {e}")
            print("尝试列出可用服务和特征值...")

            # 尝试列出所有可用服务
            services = await client.get_services()
            for service in services:
                print(f"服务: {service.uuid}")
                for char in service.characteristics:
                    print(f"  特征值: {char.uuid}")

            # 断开连接并使用模拟数据
            await client.disconnect()
            SIMULATION_MODE = True
            await simulate_hrv_data()
            return

        # 无限循环，监听 BLE 数据
        while True:
            # 不再在这里检测键盘，由事件处理
            await asyncio.sleep(0.2)  # 避免 CPU 过载

    except asyncio.TimeoutError:
        print("❌ 连接设备超时，将使用模拟数据")
        SIMULATION_MODE = True
        await simulate_hrv_data()
    except Exception as e:
        print(f"❌ 设备连接失败: {e}")
        SIMULATION_MODE = True
        await simulate_hrv_data()


# 运行程序
async def run_all_tasks():
    # 创建并运行BLE任务
    ble_task = asyncio.create_task(read_hrv())

    # 创建并运行图形更新任务
    async def update_gui():
        while True:
            update_plot(0)
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            await asyncio.sleep(0.5)

    gui_task = asyncio.create_task(update_gui())

    await ble_task


def main():
    try:
        print("初始化心率监测程序...")
        print("按空格键切换阶段，Ctrl+C 退出程序")

        # 注册空格键事件，suppress=True确保空格键被程序独占
        keyboard.on_press_key("space", handle_key_press, suppress=True)

        plt.ion()
        plt.show(block=False)

        # 运行所有任务
        asyncio.run(run_all_tasks())
    except KeyboardInterrupt:
        print("\n手动退出程序...")
    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        keyboard.unhook_all()
        save_last_stage()


if __name__ == "__main__":
    main()