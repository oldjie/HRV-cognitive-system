import tkinter as tk
import asyncio
import threading
import os
import struct
import numpy as np
import csv
import atexit
import random
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 解决 Matplotlib 后端问题
import matplotlib.pyplot as plt
from scipy import stats
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from bleak import BleakClient, BleakScanner
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IntegratedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("心率监测与认知测试综合系统")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 蓝牙设备地址
        self.hrv_device_address = ""
        self.hrv_characteristic_uuid = "00002a37-0000-1000-8000-00805f9b34fb"  # 心率数据
        
        # 数据存储
        self.all_data = []
        self.rr_interval_cache = []
        self.stage_index = 0
        self.stage_start_index = 0
        self.stage_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        self.last_stage_saved = False
        
        # 蓝牙连接状态
        self.ble_client = None
        self.is_connected = False
        self.is_collecting = False
        
        # 创建选项卡
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建各个功能的选项卡
        self.scan_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.stress_test_tab = ttk.Frame(self.notebook)
        self.stroop_test_tab = ttk.Frame(self.notebook)
        self.analyze_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.scan_tab, text="蓝牙扫描")
        self.notebook.add(self.data_tab, text="数据采集")
        self.notebook.add(self.stress_test_tab, text="压力心算测试")
        self.notebook.add(self.stroop_test_tab, text="Stroop测试")
        self.notebook.add(self.analyze_tab, text="数据分析")
        
        # 初始化各个选项卡
        self.init_scan_tab()
        self.init_data_tab()
        self.init_stress_test_tab()
        self.init_stroop_test_tab()
        self.init_analyze_tab()
        
        # 绑定选项卡切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_closing(self):
        """关闭应用程序时的处理"""
        if self.is_connected:
            asyncio.run(self.disconnect_device())
        self.root.destroy()
    
    def on_tab_changed(self, event):
        """选项卡切换时的处理"""
        current_tab = self.notebook.index(self.notebook.select())
        # 如果从数据采集切换到其他选项卡，提示用户
        if self.is_collecting and current_tab != 1:  # 1是数据采集选项卡的索引
            messagebox.showwarning("警告", "数据采集正在进行中，切换选项卡可能会影响数据采集。")
    
    # ===== 蓝牙扫描选项卡 =====
    def init_scan_tab(self):
        """初始化蓝牙扫描选项卡"""
        frame = ttk.Frame(self.scan_tab, padding="10")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="蓝牙设备扫描", font=("Arial", 16)).pack(pady=10)
        
        # 扫描按钮
        self.scan_button = ttk.Button(frame, text="扫描设备", command=self.scan_devices)
        self.scan_button.pack(pady=10)
        
        # 设备列表
        ttk.Label(frame, text="发现的设备:").pack(anchor='w', pady=5)
        self.device_listbox = tk.Listbox(frame, height=15, width=80)
        self.device_listbox.pack(fill='both', expand=True, pady=5)
        
        # 连接按钮
        self.connect_button = ttk.Button(frame, text="连接选中设备", command=self.connect_selected_device)
        self.connect_button.pack(pady=10)
        
        # 状态标签
        self.scan_status_label = ttk.Label(frame, text="状态: 就绪")
        self.scan_status_label.pack(pady=5)
    
    def scan_devices(self):
        """扫描蓝牙设备"""
        self.scan_status_label.config(text="状态: 正在扫描...")
        self.scan_button.config(state="disabled")
        self.device_listbox.delete(0, tk.END)
        
        # 在新线程中运行异步扫描
        threading.Thread(target=self.run_scan_async, daemon=True).start()
    
    def run_scan_async(self):
        """在异步环境中运行扫描"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.scan_devices_async())
    
    async def scan_devices_async(self):
        """异步扫描设备"""
        devices = await BleakScanner.discover()
        self.root.after(0, self.update_device_list, devices)
    
    def update_device_list(self, devices):
        """更新设备列表"""
        for i, device in enumerate(devices):
            self.device_listbox.insert(tk.END, f"{device.name or 'Unknown'} - {device.address}")
        
        self.scan_status_label.config(text=f"状态: 扫描完成，发现 {len(devices)} 个设备")
        self.scan_button.config(state="normal")
    
    def connect_selected_device(self):
        """连接选中的设备"""
        selected = self.device_listbox.curselection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个设备")
            return
        
        device_info = self.device_listbox.get(selected[0])
        self.hrv_device_address = device_info.split(' - ')[1]
        
        self.scan_status_label.config(text=f"状态: 已选择设备 {self.hrv_device_address}")
        messagebox.showinfo("成功", f"已选择设备: {self.hrv_device_address}\n请切换到数据采集选项卡进行连接")
        
        # 更新数据采集选项卡中的设备地址
        self.device_address_var.set(self.hrv_device_address)
    
    # ===== 数据采集选项卡 =====
    def init_data_tab(self):
        """初始化数据采集选项卡"""
        frame = ttk.Frame(self.data_tab, padding="10")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="心率数据采集", font=("Arial", 16)).pack(pady=10)
        
        # 设备地址输入
        address_frame = ttk.Frame(frame)
        address_frame.pack(fill='x', pady=5)
        ttk.Label(address_frame, text="设备地址:").pack(side='left', padx=5)
        self.device_address_var = tk.StringVar()
        ttk.Entry(address_frame, textvariable=self.device_address_var, width=40).pack(side='left', padx=5, expand=True)
        
        # 连接按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', pady=10)
        self.connect_hrv_button = ttk.Button(button_frame, text="连接设备", command=self.connect_hrv_device)
        self.connect_hrv_button.pack(side='left', padx=5)
        self.disconnect_hrv_button = ttk.Button(button_frame, text="断开连接", command=self.disconnect_hrv_device, state="disabled")
        self.disconnect_hrv_button.pack(side='left', padx=5)
        self.next_stage_button = ttk.Button(button_frame, text="下一阶段", command=self.next_stage, state="disabled")
        self.next_stage_button.pack(side='left', padx=5)
        
        # 状态和当前阶段
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill='x', pady=5)
        ttk.Label(status_frame, text="状态:").pack(side='left', padx=5)
        self.data_status_label = ttk.Label(status_frame, text="未连接")
        self.data_status_label.pack(side='left', padx=5)
        ttk.Label(status_frame, text="当前阶段:").pack(side='left', padx=20)
        self.current_stage_label = ttk.Label(status_frame, text=self.stage_labels[self.stage_index])
        self.current_stage_label.pack(side='left', padx=5)
        
        # 数据显示区域
        ttk.Label(frame, text="实时数据:").pack(anchor='w', pady=5)
        self.data_text = tk.Text(frame, height=15, width=80)
        self.data_text.pack(fill='both', expand=True, pady=5)
        
        # 保存文件名前缀
        prefix_frame = ttk.Frame(frame)
        prefix_frame.pack(fill='x', pady=5)
        ttk.Label(prefix_frame, text="文件名前缀:").pack(side='left', padx=5)
        self.file_prefix_var = tk.StringVar(value="受试者")
        ttk.Entry(prefix_frame, textvariable=self.file_prefix_var, width=20).pack(side='left', padx=5)
    
    def connect_hrv_device(self):
        """连接HRV设备"""
        if not self.device_address_var.get():
            messagebox.showwarning("警告", "请先输入设备地址")
            return
        
        self.hrv_device_address = self.device_address_var.get()
        self.data_status_label.config(text="正在连接...")
        self.connect_hrv_button.config(state="disabled")
        
        # 重置数据
        self.all_data = []
        self.rr_interval_cache = []
        self.stage_index = 0
        self.stage_start_index = 0
        self.current_stage_label.config(text=self.stage_labels[self.stage_index])
        self.data_text.delete(1.0, tk.END)
        
        # 在新线程中运行异步连接
        threading.Thread(target=self.run_connect_async, daemon=True).start()
    
    def run_connect_async(self):
        """在异步环境中运行连接"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_device())
    
    async def connect_device(self):
        """异步连接设备"""
        try:
            self.ble_client = BleakClient(self.hrv_device_address)
            await self.ble_client.connect()
            
            if self.ble_client.is_connected:
                self.is_connected = True
                self.is_collecting = True
                self.root.after(0, self.update_connection_status, True)
                
                # 开始通知
                await self.ble_client.start_notify(self.hrv_characteristic_uuid, self.notification_handler)
                
                # 保持连接
                while self.is_connected:
                    await asyncio.sleep(0.1)
                    
                # 停止通知
                if self.ble_client and self.ble_client.is_connected:
                    await self.ble_client.stop_notify(self.hrv_characteristic_uuid)
                    await self.ble_client.disconnect()
            else:
                self.root.after(0, self.update_connection_status, False)
        except Exception as e:
            self.root.after(0, self.show_connection_error, str(e))
    
    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.data_status_label.config(text="已连接，正在采集数据")
            self.connect_hrv_button.config(state="disabled")
            self.disconnect_hrv_button.config(state="normal")
            self.next_stage_button.config(state="normal")
        else:
            self.data_status_label.config(text="连接失败")
            self.connect_hrv_button.config(state="normal")
            self.disconnect_hrv_button.config(state="disabled")
            self.next_stage_button.config(state="disabled")
    
    def show_connection_error(self, error_msg):
        """显示连接错误"""
        self.data_status_label.config(text=f"连接错误: {error_msg}")
        self.connect_hrv_button.config(state="normal")
        self.disconnect_hrv_button.config(state="disabled")
        self.next_stage_button.config(state="disabled")
        messagebox.showerror("连接错误", f"连接设备时发生错误:\n{error_msg}")
    
    def disconnect_hrv_device(self):
        """断开HRV设备连接"""
        if self.is_connected:
            self.is_connected = False
            self.is_collecting = False
            threading.Thread(target=self.run_disconnect_async, daemon=True).start()
            self.data_status_label.config(text="正在断开连接...")
    
    def run_disconnect_async(self):
        """在异步环境中运行断开连接"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.disconnect_device())
        self.root.after(0, self.update_disconnection_status)
    
    async def disconnect_device(self):
        """异步断开设备连接"""
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.stop_notify(self.hrv_characteristic_uuid)
                await self.ble_client.disconnect()
            except Exception as e:
                print(f"断开连接时发生错误: {e}")
    
    def update_disconnection_status(self):
        """更新断开连接状态"""
        self.data_status_label.config(text="已断开连接")
        self.connect_hrv_button.config(state="normal")
        self.disconnect_hrv_button.config(state="disabled")
        self.next_stage_button.config(state="disabled")
        
        # 保存最后阶段的数据
        if not self.last_stage_saved and len(self.all_data) > 0:
            self.save_stage_data()
            self.last_stage_saved = True
    
    def notification_handler(self, sender, data):
        """处理BLE通知数据"""
        hr, rr_intervals = self.parse_hrv_data(data)
        self.rr_interval_cache.extend(rr_intervals)
        
        # 只保留最近60条R-R数据计算RMSSD
        if len(self.rr_interval_cache) > 60:
            self.rr_interval_cache = self.rr_interval_cache[-60:]
        
        rmssd = self.calculate_rmssd(self.rr_interval_cache)
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 记录数据
        data_item = {
            "time": current_time,
            "hr": hr,
            "rr": rr_intervals,
            "rmssd": rmssd,
            "stage": self.stage_labels[self.stage_index]
        }
        self.all_data.append(data_item)
        
        # 更新UI
        self.root.after(0, self.update_data_display, data_item)
    
    def update_data_display(self, data_item):
        """更新数据显示"""
        display_text = f"{data_item['time']} | 阶段: {data_item['stage']} | 心率: {data_item['hr']} bpm | R-R: {data_item['rr']} | RMSSD: {data_item['rmssd']}\n"
        self.data_text.insert(tk.END, display_text)
        self.data_text.see(tk.END)  # 自动滚动到最新数据
    
    def parse_hrv_data(self, data):
        """解析HRV数据"""
        data = bytearray(data)
        flags = data[0]
        
        # 解析心率
        hr = data[1]
        index = 2
        
        # 解析R-R间隔
        rr_intervals = []
        while index + 2 <= len(data):
            rr = struct.unpack("<H", data[index:index+2])[0]
            rr_intervals.append(rr)
            index += 2
        
        return hr, rr_intervals
    
    def calculate_rmssd(self, rr_intervals):
        """计算RMSSD"""
        if len(rr_intervals) < 2:
            return None
        diff_rr = np.diff(rr_intervals)
        squared_diffs = np.square(diff_rr)
        return round(float(np.sqrt(np.mean(squared_diffs))), 2)
    
    def next_stage(self):
        """进入下一阶段"""
        if self.stage_index < len(self.stage_labels) - 1:
            # 保存当前阶段数据
            self.save_stage_data()
            
            # 进入下一阶段
            self.stage_index += 1
            self.stage_start_index = len(self.all_data)
            self.current_stage_label.config(text=self.stage_labels[self.stage_index])
            messagebox.showinfo("阶段切换", f"已进入阶段 {self.stage_labels[self.stage_index]}")
        else:
            messagebox.showinfo("提示", "已达到最大阶段数")
    
    def save_stage_data(self):
        """保存当前阶段数据"""
        if len(self.all_data) <= self.stage_start_index:
            messagebox.showwarning("警告", "当前阶段没有数据可保存")
            return
        
        current_stage = self.stage_labels[self.stage_index]
        now_str = datetime.now().strftime("%m-%d_%H-%M")
        prefix = self.file_prefix_var.get().strip() or "受试者"
        filename = f"{prefix}_{now_str}_{current_stage}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["时间", "阶段", "心率 (bpm)", "R-R 间隔 (ms)", "HRV (RMSSD) (ms)"])
            for row in self.all_data[self.stage_start_index:]:
                writer.writerow([row["time"], row["stage"], row["hr"], row["rr"], row["rmssd"]])
        
        messagebox.showinfo("保存成功", f"阶段 {current_stage} 数据已保存至 {filename}")
    
    # ===== 压力心算测试选项卡 =====
    def init_stress_test_tab(self):
        """初始化压力心算测试选项卡"""
        self.stress_test_frame = ttk.Frame(self.stress_test_tab, padding="10")
        self.stress_test_frame.pack(fill='both', expand=True)
        
        ttk.Label(self.stress_test_frame, text="压力心算测试", font=("Arial", 16)).pack(pady=10)
        
        # 启动测试按钮
        self.start_stress_test_button = ttk.Button(
            self.stress_test_frame, 
            text="启动测试", 
            command=self.start_stress_test
        )
        self.start_stress_test_button.pack(pady=20)
        
        # 测试说明
        ttk.Label(
            self.stress_test_frame,
            text="测试说明：\n这是一个压力心算测试，测试过程中会显示算式，\n请判断算式是否正确，并按相应按键。",
            font=("Arial", 12),
            wraplength=600
        ).pack(pady=10)
    
    def start_stress_test(self):
        """启动压力心算测试"""
        # 清空当前选项卡内容
        for widget in self.stress_test_frame.winfo_children():
            widget.destroy()
        
        # 创建压力测试应用
        self.stress_test_app = StressTestApp(self.stress_test_frame)
    
    # ===== Stroop测试选项卡 =====
    def init_stroop_test_tab(self):
        """初始化Stroop测试选项卡"""
        self.stroop_test_frame = ttk.Frame(self.stroop_test_tab, padding="10")
        self.stroop_test_frame.pack(fill='both', expand=True)
        
        ttk.Label(self.stroop_test_frame, text="Stroop测试", font=("Arial", 16)).pack(pady=10)
        
        # 启动测试按钮
        self.start_stroop_test_button = ttk.Button(
            self.stroop_test_frame, 
            text="启动测试", 
            command=self.start_stroop_test
        )
        self.start_stroop_test_button.pack(pady=20)
        
        # 测试说明
        ttk.Label(
            self.stroop_test_frame,
            text="测试说明：\n这是一个Stroop测试，测试过程中会显示带有颜色的文字，\n请判断文字的含义与其颜色是否一致，并按相应按键。",
            font=("Arial", 12),
            wraplength=600
        ).pack(pady=10)
    
    def start_stroop_test(self):
        """启动Stroop测试"""
        # 清空当前选项卡内容
        for widget in self.stroop_test_frame.winfo_children():
            widget.destroy()
        
        # 创建Stroop测试应用
        self.stroop_test_app = StroopTestApp(self.stroop_test_frame)
    
    # ===== 数据分析选项卡 =====
    def init_analyze_tab(self):
        """初始化数据分析选项卡"""
        frame = ttk.Frame(self.analyze_tab, padding="10")
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="数据分析", font=("Arial", 16)).pack(pady=10)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(frame, text="选择数据文件")
        file_frame.pack(fill='x', pady=10, padx=5)
        
        # 阶段文件选择
        self.stage_files = {}
        for stage in ['a', 'b', 'c', 'd']:
            stage_frame = ttk.Frame(file_frame)
            stage_frame.pack(fill='x', pady=5)
            
            ttk.Label(stage_frame, text=f"阶段 {stage}:").pack(side='left', padx=5)
            file_var = tk.StringVar()
            ttk.Entry(stage_frame, textvariable=file_var, width=50).pack(side='left', padx=5, expand=True)
            ttk.Button(
                stage_frame, 
                text="浏览", 
                command=lambda s=stage, v=file_var: self.browse_file(v)
            ).pack(side='left', padx=5)
            
            self.stage_files[stage] = file_var
        
        # 分析按钮
        ttk.Button(frame, text="开始分析", command=self.analyze_data).pack(pady=10)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(frame, text="分析结果")
        result_frame.pack(fill='both', expand=True, pady=10, padx=5)
        
        # 创建选项卡用于显示不同类型的结果
        self.result_notebook = ttk.Notebook(result_frame)
        self.result_notebook.pack(fill='both', expand=True, pady=5)
        
        # 统计结果选项卡
        self.stats_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.stats_tab, text="统计结果")
        
        # 图表选项卡
        self.chart_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(self.chart_tab, text="趋势图")
    
    def browse_file(self, var):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv")]
        )
        if filename:
            var.set(filename)
    
    def analyze_data(self):
        """分析数据"""
        # 检查文件是否选择
        file_paths = {}
        for stage, var in self.stage_files.items():
            if var.get():
                file_paths[stage] = var.get()
        
        if not file_paths:
            messagebox.showwarning("警告", "请至少选择一个数据文件")
            return
        
        # 清空之前的结果
        for widget in self.stats_tab.winfo_children():
            widget.destroy()
        for widget in self.chart_tab.winfo_children():
            widget.destroy()
        
        # 读取数据并分析
        try:
            # 读取数据
            raw_data = {}
            for stage, path in file_paths.items():
                df = pd.read_csv(path)
                df.dropna(inplace=True)
                
                # 处理 R-R 间隔数据
                def parse_rr(rr_str):
                    try:
                        if isinstance(rr_str, str):
                            rr_list = eval(rr_str)  # 解析字符串列表
                            return [float(r) for r in rr_list if isinstance(r, (int, float))]
                        return []
                    except:
                        return []
                
                df["R-R 间隔 (ms)"] = df["R-R 间隔 (ms)"].apply(parse_rr)
                
                # 展开 R-R 间隔
                rr_expanded = []
                for rr_list in df["R-R 间隔 (ms)"]:
                    rr_expanded.extend(rr_list)
                
                # 存储完整数据
                raw_data[stage] = {
                    "心率 (bpm)": df["心率 (bpm)"].tolist(),
                    "R-R 间隔 (ms)": rr_expanded,  # 已展开列表
                    "HRV (RMSSD) (ms)": df["HRV (RMSSD) (ms)"].tolist(),
                }
            
            # 进行统计检验
            analysis_results = []
            stages = list(raw_data.keys())
            metrics = ["心率 (bpm)", "R-R 间隔 (ms)", "HRV (RMSSD) (ms)"]
            
            for i in range(len(stages) - 1):
                stage1, stage2 = stages[i], stages[i + 1]
                
                for metric in metrics:
                    data1 = raw_data[stage1][metric]
                    data2 = raw_data[stage2][metric]
                    
                    # 对齐数据长度
                    min_length = min(len(data1), len(data2))
                    data1, data2 = data1[:min_length], data2[:min_length]
                    
                    # 只有当数据点足够时才进行检验
                    if len(data1) < 3 or len(data2) < 3:
                        p_value, test_type = "数据不足", "跳过"
                    else:
                        # 正态性检验
                        normality_p1 = stats.shapiro(data1).pvalue
                        normality_p2 = stats.shapiro(data2).pvalue
                        
                        if normality_p1 > 0.05 and normality_p2 > 0.05:
                            # 数据服从正态分布，使用配对 t 检验
                            t_stat, p_value = stats.ttest_rel(data1, data2)
                            test_type = "配对 t 检验"
                        else:
                            # 数据非正态，使用 Wilcoxon 符号秩检验
                            t_stat, p_value = stats.wilcoxon(data1, data2)
                            test_type = "Wilcoxon 符号秩检验"
                    
                    # 记录结果
                    analysis_results.append({
                        "对比阶段": f"{stage1} → {stage2}",
                        "指标": metric,
                        "统计方法": test_type,
                        "p 值": p_value,
                        "显著性": "显著" if isinstance(p_value, float) and p_value < 0.05 else "不显著"
                    })
            
            # 显示统计结果
            result_text = tk.Text(self.stats_tab, height=20, width=80)
            result_text.pack(fill='both', expand=True, pady=10, padx=10)
            
            result_text.insert(tk.END, "统计检验结果（显著性分析）\n\n")
            result_text.insert(tk.END, f"{'对比阶段':<10}{'指标':<15}{'统计方法':<20}{'p 值':<10}{'显著性':<10}\n")
            result_text.insert(tk.END, "-" * 65 + "\n")
            
            for result in analysis_results:
                p_value = result["p 值"]
                p_str = f"{p_value:.4f}" if isinstance(p_value, float) else str(p_value)
                result_text.insert(tk.END, f"{result['对比阶段']:<10}{result['指标']:<15}{result['统计方法']:<20}{p_str:<10}{result['显著性']:<10}\n")
            
            # 绘制趋势图
            fig = plt.figure(figsize=(10, 5))
            
            # 绘制心率变化
            ax1 = fig.add_subplot(131)
            ax1.plot(stages, [np.mean(raw_data[stage]["心率 (bpm)"]) for stage in stages], marker='o', linestyle='-')
            ax1.set_xlabel("实验阶段")
            ax1.set_ylabel("平均心率 (bpm)")
            ax1.set_title("心率趋势")
            ax1.grid(True)
            
            # 绘制 R-R 间隔变化
            ax2 = fig.add_subplot(132)
            ax2.plot(stages, [np.mean(raw_data[stage]["R-R 间隔 (ms)"]) for stage in stages], marker='s', linestyle='-', color="orange")
            ax2.set_xlabel("实验阶段")
            ax2.set_ylabel("平均 R-R 间隔 (ms)")
            ax2.set_title("R-R 间隔趋势")
            ax2.grid(True)
            
            # 绘制 HRV 变化
            ax3 = fig.add_subplot(133)
            ax3.plot(stages, [np.mean(raw_data[stage]["HRV (RMSSD) (ms)"]) for stage in stages], marker='^', linestyle='-', color="green")
            ax3.set_xlabel("实验阶段")
            ax3.set_ylabel("HRV (RMSSD) (ms)")
            ax3.set_title("HRV (RMSSD) 趋势")
            ax3.grid(True)
            
            plt.tight_layout()
            
            # 在Tkinter中显示图表
            canvas = FigureCanvasTkAgg(fig, master=self.chart_tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            messagebox.showinfo("分析完成", "数据分析已完成，请查看结果选项卡")
            
        except Exception as e:
            messagebox.showerror("分析错误", f"分析数据时发生错误:\n{str(e)}")


# ===== StressTestApp类 =====
class StressTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("压力心算测试")
        
        self.grade_choice = None
        self.problems = []
        self.current_problem = 0
        self.answered = False
        self.after_id = None
        self.started = False
        self.problem_answers = []
        self.result_shown = False
        
        self.choice_label = tk.Label(
            root,
            text="请选择测试档次：\n1. 小学档（50道加减法）\n2. 中学档（50道加减乘除混搭）",
            font=("Arial", 24),
            wraplength=700
        )
        self.choice_label.pack(pady=100)
        
        self.root.bind("<Key>", self.handle_choice)
    
    def handle_choice(self, event):
        try:
            choice = int(event.char)
            if choice == 1:
                self.grade_choice = "小学档"
                self.problems = self.generate_primary_problems(50)
            elif choice == 2:
                self.grade_choice = "中学档"
                self.problems = self.generate_middle_problems(50)
            else:
                return
            
            self.choice_label.pack_forget()
            self.start_test()
        except ValueError:
            pass
    
    def generate_primary_problems(self, num):
        problems = []
        for _ in range(num):
            a = random.randint(1, 100)
            b = random.randint(1, a)  # 保证减法结果非负
            operator = random.choice(['+', '-'])
            if operator == '+':
                correct_result = a + b
            else:
                correct_result = a - b
            if random.choice([True, False]):
                equation = f"{a} {operator} {b} = {correct_result}"
                is_correct = True
            else:
                offset = random.choice([-2, -1, 1, 2])
                wrong_result = correct_result + offset
                equation = f"{a} {operator} {b} = {wrong_result}"
                is_correct = False
            problems.append((equation, is_correct))
        return problems
    
    def generate_middle_problems(self, num):
        problems = []
        operators = ['+', '-', '*', '/']
        for _ in range(num):
            operator = random.choice(operators)
            if operator == '+':
                a = random.randint(1, 100)
                b = random.randint(1, 100)
            elif operator == '*':
                a = random.randint(1, 30)
                b = random.randint(1, 30)
            elif operator == '-':
                a = random.randint(1, 200)
                b = random.randint(1, a)  # 保证减法结果非负
            else:  # 除法
                while True:
                    a = random.randint(2, 200)  # 被除数从 2 开始，保证商大于 1
                    b = random.randint(1, a - 1)  # 除数小于被除数
                    quotient = a // b
                    if a % b == 0 and quotient > 1:
                        break
            
            if operator == '+':
                correct_result = a + b
            elif operator == '-':
                correct_result = a - b
            elif operator == '*':
                correct_result = a * b
            else:
                correct_result = a // b
            
            if random.choice([True, False]):
                equation = f"{a} {operator} {b} = {correct_result}"
                is_correct = True
            else:
                offset = random.choice([-2, -1, 1, 2, -3, 3, -13, -12, -11, -10, 10, 11, 12, 13, -20, 20, -21, -22, 21, 22])
                wrong_result = correct_result + offset
                equation = f"{a} {operator} {b} = {wrong_result}"
                is_correct = False
            problems.append((equation, is_correct))
        return problems
    
    def start_test(self):
        if not self.started:
            self.started = True
            self.introduction_label = tk.Label(
                self.root,
                text=f"你选择了{self.grade_choice}。在本次压力心算测试中，\n请判断屏幕上显示的算式是否正确。\n如果正确，请按 'N' 键；如果错误，请按 'M' 键。\n每题限时 4 秒，超时将显示\"超时\"。\n按空格开始测试。",
                font=("Arial", 24),
                wraplength=700
            )
            self.introduction_label.pack(pady=100)
            self.root.bind("<space>", self.begin_test)
            self.root.bind("<Key>", self.handle_key)
    
    def begin_test(self, event=None):
        self.introduction_label.pack_forget()
        self.equation_label = tk.Label(self.root, font=("Arial", 48))
        self.equation_label.pack(pady=100)
        self.feedback_label = tk.Label(self.root, font=("Arial", 24))
        self.feedback_label.pack()
        self.show_problem()
    
    def show_problem(self):
        self.answered = False
        if self.current_problem >= len(self.problems) and not self.result_shown:
            self.show_result()
            return
        
        equation, is_correct = self.problems[self.current_problem]
        self.equation_label.config(text=equation)
        self.current_is_correct = is_correct
        
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(4000, self.timeout)
    
    def check_answer(self, event):
        if self.answered:
            return
        self.answered = True
        
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        user_key = event.keysym.lower()
        self.problem_answers.append(user_key)
        is_correct_answer = (
                (user_key == "n" and self.current_is_correct) or
                (user_key == "m" and not self.current_is_correct)
        )
        
        if is_correct_answer:
            self.feedback_label.config(text="正确", fg="green", font=("Arial", 48))
        else:
            self.feedback_label.config(text="错误", fg="red", font=("Arial", 48))
        
        self.root.after(500, self.next_problem)
    
    def timeout(self):
        if self.answered:
            return
        self.answered = True
        self.problem_answers.append(None)  # 超时记录为 None
        self.feedback_label.config(text="超时", fg="red", font=("Arial", 48))
        self.root.after(500, self.next_problem)
    
    def next_problem(self):
        self.current_problem += 1
        self.feedback_label.config(text="")
        self.show_problem()
    
    def show_result(self):
        correct_count = 0
        for i in range(len(self.problems)):
            _, is_correct = self.problems[i]
            answer = self.problem_answers[i]
            if answer is not None and ((answer == "n" and is_correct) or (answer == "m" and not is_correct)):
                correct_count += 1
        accuracy = correct_count / len(self.problems) * 100
        self.equation_label.pack_forget()
        self.feedback_label.pack_forget()
        
        self.result_label = tk.Label(self.root, text=f"答题正确率: {accuracy:.2f}%", fg="red", font=("Arial", 48))
        self.result_label.pack(pady=100)
        self.result_shown = True  # 标记结果已显示
    
    def handle_key(self, event):
        if not self.answered and not self.result_shown:
            if event.keysym.lower() in ['n', 'm']:
                self.check_answer(event)


# ===== StroopTestApp类 =====
class StroopTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stroop 测试")
        
        self.color_words = ["红", "绿", "蓝", "黄", "紫", "黑"]
        self.color_map = {
            "红": "red",
            "绿": "green",
            "蓝": "blue",
            "黄": "yellow",
            "紫": "purple",
            "黑": "black"
        }
        
        # 用于存储随机生成的题目列表
        self.problems = []
        self.current_problem_idx = 0
        
        # 标识当前题是否已回答或已超时
        self.answered = False
        self.after_id = None
        
        # 测试是否已经启动
        self.started = False
        # 是否已经显示了自评环节
        self.self_assessment_shown = False
        
        # 介绍说明 Label
        self.introduction_label = tk.Label(
            self.root,
            text=(
                '欢迎进入中文版本的 Stroop 测试！\n\n'
                '程序会随机显示一个颜色词（如"红"），并以某种字体颜色呈现。\n'
                '如果颜色词含义与其字体颜色一致（例如"红"用红色字体），请按 \'N\' 键。\n'
                '如果颜色词含义与其字体颜色不一致（例如"红"用绿色字体），请按 \'M\' 键。\n'
                '每题限时 4 秒，超时将自动显示"超时"。\n\n'
                '完成所有题目后，会要求您进行 1 - 5 的焦虑/压力自评。\n\n'
                '按空格键开始测试。'
            ),
            font=("Arial", 20),
            wraplength=700,
            justify="left"
        )
        self.introduction_label.pack(pady=50)
        
        # 绑定空格键以启动测试
        self.root.bind("<space>", self.start_test)
    
    def start_test(self, event=None):
        if not self.started:
            self.started = True
            self.introduction_label.pack_forget()
            
            # 生成测试题目
            self.generate_problems(num=20)
            
            # 显示题目的 Label
            self.word_label = tk.Label(self.root, font=("Arial", 48))
            self.word_label.pack(pady=50)
            
            # 反馈 Label
            self.feedback_label = tk.Label(self.root, font=("Arial", 36))
            self.feedback_label.pack(pady=20)
            
            # 绑定按键，用于答题：N/M
            self.root.bind("<Key>", self.handle_key)
            
            # 显示第一题
            self.show_problem()
    
    def generate_problems(self, num=20):
        self.problems = []
        for _ in range(num):
            word = random.choice(self.color_words)
            color_name = random.choice(self.color_words)
            is_correct = (word == color_name)  # True 表示文字与颜色含义一致
            
            self.problems.append(
                (word, self.color_map[color_name], is_correct)
            )
        
        random.shuffle(self.problems)
    
    def show_problem(self):
        self.answered = False
        
        if self.current_problem_idx >= len(self.problems):
            self.show_self_assessment()
            return
        
        word, font_color, is_correct = self.problems[self.current_problem_idx]
        # 设置 Label 显示内容
        self.word_label.config(text=word, fg=font_color)
        self.feedback_label.config(text="")
        
        # 每题限时 4 秒
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(4000, self.timeout)
    
    def handle_key(self, event):
        # 如果已经进入自评阶段，则处理自评输入
        if self.self_assessment_shown:
            self.handle_self_assessment_input(event)
            return
        
        # 如果当前题已回答或超时，不再处理输入
        if self.answered:
            return
        
        user_key = event.keysym.lower()
        if user_key not in ["n", "m"]:
            return
        
        self.answered = True
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        _, _, is_correct = self.problems[self.current_problem_idx]
        # 'N' 表示用户判断一致，'M' 表示不一致
        user_judgement = (user_key == "n")
        
        if user_judgement == is_correct:
            self.feedback_label.config(text="正确", fg="green")
        else:
            self.feedback_label.config(text="错误", fg="red")
        
        self.root.after(500, self.next_problem)
    
    def timeout(self):
        # 超时处理
        if self.answered:
            return
        self.answered = True
        self.feedback_label.config(text="超时", fg="red")
        self.root.after(500, self.next_problem)
    
    def next_problem(self):
        # 进入下一题
        self.current_problem_idx += 1
        self.show_problem()
    
    def show_self_assessment(self):
        # 显示自评环节
        self.self_assessment_shown = True
        self.word_label.pack_forget()
        self.feedback_label.pack_forget()
        
        self.assessment_label = tk.Label(
            self.root,
            text="测试结束！\n\n请输入 1 - 5 的数字进行焦虑/压力等级自评：",
            font=("Arial", 24)
        )
        self.assessment_label.pack(pady=50)
        
        self.assessment_result_label = tk.Label(self.root, font=("Arial", 24))
        self.assessment_result_label.pack(pady=20)
    
    def handle_self_assessment_input(self, event):
        try:
            level = int(event.char)
            if 1 <= level <= 5:
                self.assessment_result_label.config(
                    text=f"焦虑/压力等级已记录：{level} 级"
                )
        except ValueError:
            pass


# ===== 主程序入口 =====
if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedApp(root)
    root.mainloop()