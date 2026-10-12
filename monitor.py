#!/usr/bin/env python3
"""System monitor: CPU, memory, disk, network, and top processes."""

import time
import datetime
import psutil


INTERVAL = 5  # seconds between updates
BAR_WIDTH = 30


def make_bar(percent: float, width: int = BAR_WIDTH) -> str:
    filled = int(width * percent / 100)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {percent:.1f}%"


def bytes_to_human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def collect() -> dict:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")

    net_before = psutil.net_io_counters()
    time.sleep(1)
    net_after = psutil.net_io_counters()
    net_sent = net_after.bytes_sent - net_before.bytes_sent
    net_recv = net_after.bytes_recv - net_before.bytes_recv

    temps = {}
    try:
        raw = psutil.sensors_temperatures()
        for key, entries in raw.items():
            if entries:
                temps[key] = entries[0].current
    except AttributeError:
        pass

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    top5 = sorted(procs, key=lambda x: x["cpu_percent"] or 0, reverse=True)[:5]

    return {
        "cpu": cpu,
        "mem": mem,
        "swap": swap,
        "disk": disk,
        "net_sent": net_sent,
        "net_recv": net_recv,
        "temps": temps,
        "top5": top5,
    }


def render(data: dict) -> None:
    print("\033[2J\033[H", end="")  # clear screen
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== System Monitor  {now} ===\n")

    print(f"CPU        {make_bar(data['cpu'])}")

    m = data["mem"]
    print(f"RAM        {make_bar(m.percent)}  ({bytes_to_human(m.used)} / {bytes_to_human(m.total)})")

    s = data["swap"]
    print(f"Swap       {make_bar(s.percent)}  ({bytes_to_human(s.used)} / {bytes_to_human(s.total)})")

    d = data["disk"]
    print(f"Disk  /    {make_bar(d.percent)}  ({bytes_to_human(d.used)} / {bytes_to_human(d.total)})")

    print(f"\nNetwork    ↑ {bytes_to_human(data['net_sent'])}/s   ↓ {bytes_to_human(data['net_recv'])}/s")

    if data["temps"]:
        print("\nTemperatures:")
        for sensor, temp in data["temps"].items():
            print(f"  {sensor:<20} {temp:.1f} °C")

    print("\nTop 5 processes by CPU:")
    print(f"  {'PID':>6}  {'CPU%':>6}  {'MEM%':>6}  Name")
    for p in data["top5"]:
        print(f"  {p['pid']:>6}  {p['cpu_percent'] or 0:>6.1f}  {p['memory_percent'] or 0:>6.1f}  {p['name']}")

    print("\n[Ctrl+C to quit]")


def main() -> None:
    print("Starting system monitor... (press Ctrl+C to stop)")
    try:
        while True:
            data = collect()
            render(data)
            time.sleep(max(0, INTERVAL - 2))  # collect() already sleeps ~2 s
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
