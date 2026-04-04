# Project Release Summary

## 项目概述

**项目名称**: HRV Cognitive Testing System
**当前版本**: v1.0.0

### 项目解决什么问题

这是一个心率变异性（HRV）监测与认知测试综合系统，专为心理生理学研究设计。系统通过 BLE 连接心率带设备（如 KYTO HRV），实时采集心率和 R-R 间隔数据，同时提供标准化的认知测试（Stroop 测试、压力心算测试），适用于：

- 心率变异性（HRV）与认知表现的关系研究
- 压力与认知控制的行为实验
- 心理生理学实验的多阶段数据采集与分析

### 当前版本亮点

1. **BLE 心率监测**: 支持 KYTO HRV 等标准 HRP 兼容设备，无需专用软件
2. **实时 HRV 计算**: 基于 RMSSD 算法的实时心率变异性计算
3. **多阶段实验设计**: 支持最多 10 个实验阶段的自动标记与数据分割
4. **标准化认知测试**: 内置 Stroop 测试和压力心算测试，支持难度分级
5. **统计分析模块**: 内置 t 检验、Wilcoxon 符号秩检验、ANOVA 等常用统计方法
6. **一键数据导出**: CSV 格式导出，便于后续分析

### 后续计划

- [ ] 添加更多 HRV 指标（SDNN, pNN50, 频域分析）
- [ ] 支持实验设计的配置文件导入
- [ ] 添加数据质量评估指标
- [ ] 支持多被试批量数据管理
- [ ] 导出兼容 SPSS/Excel 的格式

---

## GitHub 仓库元数据建议

### 仓库名称

```
hrv-cognitive-system
```

### 英文 Description

An integrated HRV monitoring and cognitive testing system for psychophysiological research. Supports KYTO HRV and other BLE heart rate straps, real-time RMSSD calculation, multi-stage experiments, Stroop test, and statistical analysis.

### 中文 Description

心率变异性（HRV）监测与认知测试综合系统，适用于心理生理学研究。支持 KYTO HRV 等蓝牙心率带，实时 RMSSD 计算，多阶段实验设计，S

troop 测试，统计分析和可视化。

### Topics

```
hrv heart-rate-variability ble bluetooth low-energy psychophysiology stroop-test cognitive-science research-tool python kyto-hrv
```

### Homepage

(留空或指向文档)

---

## 首版 Release Notes 草稿

**Tag**: v1.0.0
**Title**: Initial Release - HRV Cognitive Testing System

**Body**:

### 主要功能

- 初始版本发布
- BLE 心率监测（支持 KYTO HRV 等设备）
- 实时 RMSSD HRV 计算
- 多阶段实验数据采集（最多 10 阶段）
- Stroop 认知测试（中文颜色词版本）
- 压力心算测试（小学/中学两档难度）
- 统计分析模块（t 检验、Wilcoxon、ANOVA）
- 实时数据可视化
- 命令行数据采集工具

### 支持的设备

- KYTO HRV 系列心率带
- 其他支持 Heart Rate Profile (HRP) 的 BLE 心率设备

### 系统要求

- Python 3.8+
- 蓝牙 4.0+ (BLE)
- Windows / macOS / Linux
