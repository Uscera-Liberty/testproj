# testproj — System Monitor

A lightweight terminal system-monitor written in Python.

## What it shows

| Metric | Details |
|--------|---------|
| CPU | Overall usage % with ASCII progress bar |
| RAM / Swap | Used / total with usage bar |
| Disk (`/`) | Used / total with usage bar |
| Network | Upload and download speed (bytes/s) |
| Temperatures | All sensors reported by the OS (if available) |
| Top 5 processes | Sorted by CPU %, with PID, CPU %, MEM % and name |

The screen refreshes every **5 seconds** (configurable via `INTERVAL` at the top of the script).

## Requirements

- Python 3.8+
- [psutil](https://github.com/giampaolo/psutil)

```bash
pip install psutil
```

## Usage

```bash
python monitor.py
```

Press **Ctrl+C** to stop.

## Configuration

Open `monitor.py` and change the constant at the top:

```python
INTERVAL = 5   # seconds between full refreshes
BAR_WIDTH = 30 # character width of progress bars
```
