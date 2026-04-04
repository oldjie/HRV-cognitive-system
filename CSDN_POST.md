# 【项目分享】开源 HRV 认知测试系统：心率变异性监测与心理科学实验的完美结合

## 前言

做认知心理学或心理生理学研究的朋友都知道，HRV（心率变异性）是一个非常重要的指标，它可以反映自主神经系统的活跃程度，进而评估个体的压力状态和认知控制能力。

今天要分享的是我开源的一个**HRV 认知测试系统**，它可以：
- 通过蓝牙连接心率带，实时采集 HRV 数据
- 提供标准化的 Stroop 测试和压力心算测试
- 支持多阶段实验设计
- 内置统计分析功能

项目地址：https://github.com/oldjie/HRV-cognitive-system

---

## 一、项目背景与解决的问题

在做 HRV 与认知表现的关系研究时，我需要：

1. 同时采集心率数据和认知测试表现
2. 支持多阶段的实验设计（比如基线期-压力期-恢复期）
3. 数据能直接用于统计分析

市面上有一些商业设备可以做到，但往往：
- 价格昂贵
- 软件封闭，不好定制
- 数据导出麻烦

所以我决定自己写一个。

---

## 二、系统架构

### 2.1 硬件要求

本系统支持 **KYTO HRV** 系列心率带，以及其他使用 Heart Rate Profile (HRP) 的 BLE 心率设备。

核心原理：
- 心率带通过 BLE 广播心率数据和 R-R 间隔
- 我们订阅 BLE 特征值，获取原始数据
- 计算 RMSSD（相邻 R-R 间隔差值的均方根）作为 HRV 指标

设备 MAC 地址格式：`XX:XX:XX:XX:XX:XX`

### 2.2 软件架构

```
integrated_app.py      # GUI 主程序（Tkinter）
├── 蓝牙扫描选项卡      # 发现并连接心率带
├── 数据采集选项卡      # 多阶段 HRV 数据采集
├── Stroop 测试选项卡   # 认知干扰测试
├── 心算测试选项卡     # 压力心算测试
└── 数据分析选项卡      # 统计分析+可视化
```

---

## 三、核心功能详解

### 3.1 BLE 心率数据采集

核心代码（collect.py）：

```python
from bleak import BleakClient
import struct
import numpy as np

HRV_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"
HRV_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

def calculate_rmssd(rr_intervals):
    """计算 RMSSD：相邻 R-R 间隔差值的均方根"""
    if len(rr_intervals) < 2:
        return None
    diff_rr = np.diff(rr_intervals)
    squared_diffs = np.square(diff_rr)
    return round(float(np.sqrt(np.mean(squared_diffs))), 2)

def parse_hrv_data(data):
    """解析 BLE 设备数据"""
    data = bytearray(data)
    hr = data[1]
    rr_intervals = []
    index = 2
    while index + 2 <= len(data):
        rr = struct.unpack("<H", data[index:index + 2])[0]
        rr_intervals.append(rr)
        index += 2
    return hr, rr_intervals

async def read_hrv():
    async with BleakClient(HRV_DEVICE_ADDRESS) as client:
        await client.start_notify(HRV_CHARACTERISTIC_UUID, on_hrv_data)
        while True:
            await asyncio.sleep(0.2)
```

采集的数据格式（CSV）：
- 时间戳
- 实验阶段（a-j）
- 心率（bpm）
- R-R 间隔（ms）
- HRV RMSSD（ms）

### 3.2 Stroop 测试

经典的 Stroop 效应测试，汉字版本：

```python
class StroopTestApp:
    def __init__(self, root):
        self.color_words = ["红", "绿", "蓝", "黄", "紫", "黑"]
        self.color_map = {
            "红": "red", "绿": "green", "蓝": "blue",
            "黄": "yellow", "紫": "purple", "黑": "black"
        }

    def generate_problems(self, num=20):
        for _ in range(num):
            word = random.choice(self.color_words)
            color_name = random.choice(self.color_words)
            is_congruent = (word == color_name)  # 一致性判断
            self.problems.append((word, self.color_map[color_name], is_congruent))
```

测试逻辑：
- 显示汉字颜色词，字体颜色可能与词义一致或不一致
- 被试按 'N' 表示一致，'M' 表示不一致
- 每题限时 4 秒，超时自动跳转

### 3.3 压力心算测试

两档难度：
- 小学档：50 道加减法
- 中学档：50 道加减乘除混搭

```python
def generate_middle_problems(self, num):
    problems = []
    operators = ['+', '-', '*', '/']
    for _ in range(num):
        operator = random.choice(operators)
        # 生成题目...
        # 50% 概率放正确答案，50% 放错误答案
        is_correct = random.choice([True, False])
        problems.append((equation, is_correct))
    return problems
```

### 3.4 统计分析

内置多种统计方法（analyze.py）：

```python
from scipy import stats

# 正态性检验
normality_p1 = stats.shapiro(data1).pvalue
normality_p2 = stats.shapiro(data2).pvalue

if normality_p1 > 0.05 and normality_p2 > 0.05:
    # 配对 t 检验
    t_stat, p_value = stats.ttest_rel(data1, data2)
else:
    # Wilcoxon 符号秩检验
    t_stat, p_value = stats.wilcoxon(data1, data2)
```

支持的分析：
- Shapiro-Wilk 正态性检验
- 配对 t 检验 / Wilcoxon 符号秩检验
- 单因素方差分析（ANOVA）
- 效应量计算（Cohen's d, η²）

---

## 四、使用方法

### 4.1 环境搭建

```bash
# 克隆项目
git clone https://github.com/oldjie/HRV-cognitive-system.git
cd HRV-cognitive-system

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4.2 扫描设备

```bash
python scan.py
```

会列出所有发现的 BLE 设备，找到你的心率带，记下 MAC 地址。

### 4.3 运行主程序

```bash
python integrated_app.py
```

GUI 界面会显示 5 个选项卡，按顺序操作：
1. 蓝牙扫描 → 连接心率带
2. 切换到数据采集 → 开始实验
3. 按空格键切换实验阶段
4. 实验结束后进行认知测试
5. 在数据分析选项卡导入 CSV 进行统计分析

### 4.4 命令行采集模式

如果不需要 GUI，可以用命令行模式：

```bash
python collect.py
# 按空格键标记阶段
# Ctrl+C 退出，自动保存数据
```

---

## 五、数据示例

采集的 CSV 文件示例：

```csv
时间,阶段,心率 (bpm),R-R 间隔 (ms),HRV (RMSSD) (ms)
14:23:45,a,"[823, 815, 819]",48.32
14:23:46,a,"[818, 822, 820]",47.85
14:23:47,b,"[798, 802, 795]",52.17
...
```

导入数据分析选项卡后，会输出：

```
对比阶段    指标              统计方法           p 值     显著性
--------------------------------------------------------------
a → b      心率 (bpm)        配对 t 检验       0.0234   显著
a → b      HRV (RMSSD)       Wilcoxon 符号秩   0.0156   显著
```

---

## 六、后续开发计划

- [ ] 添加频域分析（LF/HF 功率谱）
- [ ] 支持更多 HRV 指标（SDNN, pNN50）
- [ ] 实验配置文件导入
- [ ] 多被试批量管理
- [ ] 导出 SPSS 兼容格式

---

## 七、开源心得

这个项目从想法到实现大概花了两周时间，主要踩过的坑：

1. **BLE 连接不稳定**：Windows 和 Linux 的 BLE 实现有差异，最终用了 `bleak` 库解决跨平台问题
2. **中文字符编码**：Python 字符串中的中文引号导致语法错误，后来统一用单引号包裹字符串
3. **多线程/异步**：GUI 和 BLE 采集需要分离线程，用了 `asyncio` + `threading` 结合

---

## 结语

如果你也在做 HRV 或认知神经科学相关的研究，欢迎使用这个工具。有问题可以提 Issue，也欢迎 PR。

项目地址：https://github.com/oldjie/HRV-cognitive-system

---

**标签建议**：
- #HRV #心率变异性 #心理生理学 #BLE #蓝牙 #Python #Stroop测试 #认知科学 #开源 #KYTO

---

### 版本一：热情邀请版（适合社交媒体）

> 👋 如果这个项目对你有帮助，点个 Star 支持下吧！
> 有任何问题或建议，欢迎在 GitHub 提 Issue。
> 也欢迎交流学习，共同进步！

### 版本二：克制专业版（适合技术社区）

> 项目已开源至 GitHub，MIT 协议。
> 欢迎 Issues 和 Pull Requests。
