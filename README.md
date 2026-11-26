<h1 align="center">HRV Cognitive Testing System</h1>

<p align="center">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">简体中文</a>
</p>

An integrated system for heart rate variability (HRV) monitoring combined with cognitive tests (Stroop test and mental arithmetic stress test). Designed for psychophysiological research.

> **Supported Devices**: Optimized for **KYTO HRV** heart rate monitors and other standard BLE heart rate monitoring devices using the Heart Rate Profile (HRP).

## Features

- **BLE Heart Rate Monitoring**: Connect to standard BLE heart rate monitoring devices via Bluetooth. **Compatible with KYTO HRV devices** and other HRP-compliant heart rate monitoring devices
- **Real-time HRV Calculation**: Live RMSSD calculation from R-R intervals
- **Multi-stage Experiment Support**: Press space to mark stage transitions during data collection
- **Stress Arithmetic Test**: Mental calculation test with difficulty levels (primary/middle school)
- **Stroop Test**: Classic cognitive interference test with Chinese color words
- **Statistical Analysis**: Built-in t-test, Wilcoxon, ANOVA with publication-ready output
- **Data Visualization**: Trend charts for HR, R-R intervals, and HRV across stages

## Project Structure

```
.
├── integrated_app.py      # Main integrated application (GUI)
├── collect.py             # CLI data collection tool
├── realtime.py            # Real-time monitoring with visualization
├── scan.py                # BLE device scanner
├── analyze.py             # Statistical analysis script
├── strooptest.py          # Standalone Stroop test
├── cal_test.py            # Standalone stress arithmetic test
├── used/                  # Utility scripts for data processing
│   ├── calc_hr_hrv.py     # Batch HR/HRV statistics
│   ├── mean_analyze.py    # Group comparison analysis
│   ├── adhd_analyze.py    # ADHD cohort analysis
│   └── ...
├── requirements.txt
└── .env.example
```

## Supported BLE Devices

This project is designed to work with **KYTO HRV** heart rate monitors and other standard Bluetooth Low Energy (BLE) heart rate monitoring devices that implement the **Heart Rate Profile (HRP)**.

### Compatible Devices

- **KYTO HRV** series heart rate monitors
- Other HRP-compliant BLE heart rate monitoring devices

### Device Requirements

- Bluetooth 4.0 or higher (BLE support)
- Heart Rate Profile (HRP) compliant
- R-R interval measurement capability (for HRV calculation)

### Finding Your Device MAC Address

```bash
python scan.py
```

This will list all discoverable BLE devices. Look for your KYTO HRV device (or other heart rate monitoring device) and note its MAC address (format: `XX:XX:XX:XX:XX:XX`).

## Installation

### Prerequisites

- Python 3.8+
- BLE-enabled device (Linux, macOS, or Windows with BLE support)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/hrv-cognitive-system.git
cd hrv-cognitive-system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```
bleak>=0.20.0
keyboard>=0.13.5
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
scikit-learn>=1.0.0
```

## Usage

### 1. Scan for BLE Devices

```bash
python scan.py
```

This will discover all nearby BLE devices. Look for your KYTO HRV or other heart rate monitoring device.

### 2. Run Integrated GUI Application

```bash
python integrated_app.py
```

The GUI provides 5 tabs:
- **Bluetooth Scan**: Discover and connect to BLE heart rate devices (KYTO HRV, etc.)
- **Data Collection**: Collect HRV data with multi-stage markers
- **Stress Arithmetic Test**: Mental calculation stress test
- **Stroop Test**: Cognitive interference test
- **Data Analysis**: Import CSV files and perform statistical analysis

### 3. CLI Data Collection

```bash
python collect.py
```

Press **Space** to mark stage transitions. Press **Ctrl+C** to exit.

### 4. Real-time Monitoring with Visualization

```bash
python realtime.py
```

Opens a live plotting window showing heart rate and HRV in real-time from your KYTO HRV monitoring device.

### 5. Standalone Tests

```bash
# Stroop Test
python strooptest.py

# Stress Arithmetic Test
python cal_test.py
```

## Data Format

Collected CSV files contain:
- `时间`: Timestamp
- `阶段`: Experiment stage label (a-j)
- `心率 (bpm)`: Heart rate in beats per minute
- `R-R 间隔 (ms)`: R-R interval in milliseconds (list)
- `HRV (RMSSD) (ms)`: Root mean square of successive differences

## Configuration

Copy `.env.example` to `.env` and set your BLE device address:

```bash
cp .env.example .env
# Edit .env with your device MAC address (e.g., KYTO HRV device address)
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- HRV measurement follows IEEE 11073 standards for personal health devices
- Stroop Test: Stroop, J.R. (1935). Studies of interference in serial verbal reactions.
- RMSSD calculation follows HRV guidelines from the European Heart Journal.
