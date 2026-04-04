# HRV 认知测试系统

[English](README.md) | [简体中文](README.zh-CN.md)

心率变异性（HRV）监测与认知测试综合系统，适用于心理生理学研究。

> **支持设备**：专为 **KYTO HRV** 心率带及其他标准 BLE 心率带设计，兼容所有使用心率配置（HRP）的设备。

## 功能特性

- **蓝牙心率监测**：通过 BLE 连接心率设备。**支持 KYTO HRV** 及所有 HRP 兼容心率带
- **实时 HRV 计算**：基于 R-R 间隔实时计算 RMSSD
- **多阶段实验支持**：空格键标记实验阶段切换
- **压力心算测试**：小学/中学两档难度的心算压力测试
- **Stroop 测试**：中文颜色词的认知干扰测试
- **统计分析**：内置 t 检验、Wilcoxon 符号秩检验、ANOVA，支持组间比较
- **数据可视化**：多阶段心率、R-R 间隔、HRV 趋势图

## 目录结构

```
.
├── integrated_app.py      # 主程序（GUI 综合应用）
├── collect.py             # 命令行数据采集工具
├── realtime.py            # 实时心率监测+可视化
├── scan.py                # BLE 设备扫描
├── analyze.py             # 统计分析脚本
├── strooptest.py          # 独立 Stroop 测试
├── cal_test.py            # 独立压力心算测试
├── used/                  # 数据处理工具脚本
│   ├── calc_hr_hrv.py     # 批量 HR/HRV 统计
│   ├── mean_analyze.py     # 组间比较分析
│   ├── adhd_analyze.py     # ADHD 队列分析
│   └── ...
├── requirements.txt
└── .env.example
```

## 支持的 BLE 设备

本项目设计用于支持 **KYTO HRV** 心率带及其他标准蓝牙低功耗（BLE）心率带，兼容所有使用**心率配置（Heart Rate Profile, HRP）**的设备。

### 兼容设备

- **KYTO HRV** 系列心率带
- 其他 HRP 兼容的 BLE 心率设备

### 设备要求

- 蓝牙 4.0 或更高版本（支持 BLE）
- 支持心率配置（HRP）
- 支持 R-R 间隔测量（用于 HRV 计算）

### 获取设备 MAC 地址

```bash
python scan.py
```

这将列出所有可发现的 BLE 设备。找到您的 KYTO HRV 设备（或心率带），记下其 MAC 地址（格式：`XX:XX:XX:XX:XX:XX`）。

## 安装

### 环境要求

- Python 3.8+
- 支持 BLE 蓝牙的设备（Linux、macOS 或 Windows）

### 步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/hrv-cognitive-system.git
cd hrv-cognitive-system

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 依赖项

```
bleak>=0.20.0
keyboard>=0.13.5
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
scikit-learn>=1.0.0
```

## 使用方式

### 1. 扫描 BLE 设备

```bash
python scan.py
```

这将发现附近所有 BLE 设备。请寻找您的 KYTO HRV 或其他心率设备。

### 2. 运行 GUI 综合应用

```bash
python integrated_app.py
```

GUI 提供 5 个选项卡：
- **蓝牙扫描**：发现并连接 BLE 心率设备（KYTO HRV 等）
- **数据采集**：多阶段标记的 HRV 数据采集
- **压力心算测试**：心算压力测试
- **Stroop 测试**：认知干扰测试
- **数据分析**：导入 CSV 文件进行统计分析

### 3. 命令行数据采集

```bash
python collect.py
```

按 **空格键** 标记阶段切换，按 **Ctrl+C** 退出。

### 4. 实时监测+可视化

```bash
python realtime.py
```

打开实时绘图窗口，显示 KYTO HRV 设备的心率和 HRV 动态变化。

### 5. 独立测试程序

```bash
# Stroop 测试
python strooptest.py

# 压力心算测试
python cal_test.py
```

## 数据格式

采集的 CSV 文件包含以下列：
- `时间`：时间戳
- `阶段`：实验阶段标签（a-j）
- `心率 (bpm)`：每分钟心跳数
- `R-R 间隔 (ms)`：R-R 间隔（毫秒，列表格式）
- `HRV (RMSSD) (ms)`：相邻 R-R 间隔差值的均方根

## 配置

复制 `.env.example` 为 `.env`，设置 BLE 设备地址：

```bash
cp .env.example .env
# 编辑 .env，填入您的设备 MAC 地址（例如 KYTO HRV 设备地址）
```

## 常见问题

**Q: 连接 BLE 设备失败？**
A: 确保设备已配对且处于广播状态，Windows 用户可能需要安装 BLE 驱动。

**Q: 实时绘图窗口不显示？**
A: 检查 matplotlib 后端配置，Linux 无 GUI 环境可使用 `matplotlib.use('Agg')`。

**Q: 如何进行多阶段实验？**
A: 在数据采集中按空格键切换阶段，程序会自动保存每个阶段的数据。

## 贡献指南

欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解投稿指南。

## 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件。

## 参考文献

- HRV 测量遵循 IEEE 11073 个人健康设备标准
- Stroop 测试：Stroop, J.R. (1935). Studies of interference in serial verbal reactions.
- RMSSD 计算依据欧洲心脏学会 HRV 指南。
