import os
import signal
import time

import psutil

from .monitor import monitor, start_monitor
from .safety import check_allowed


def get_process_metrics(top_n=10, name_filter=None, min_cpu=0.0,
                        min_running_seconds=0, sort_by="cpu",
                        avg_window_seconds=0):
    """List processes with CPU%, RAM%, run time. Highest first.

    avg_window_seconds > 0 uses the background monitor to give the AVERAGE CPU
    over that many seconds (for example 300 = the last 5 minutes).
    """
    window_mode = bool(avg_window_seconds and avg_window_seconds > 0)

    if window_mode:
        start_monitor()                      # make sure the monitor is running
    else:
        # Prime the CPU counters, wait 1 second, then read for real.
        for p in psutil.process_iter():
            try:
                p.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(1)

    rows = []
    attrs = ['pid', 'name', 'username', 'cmdline', 'cpu_percent',
             'memory_percent', 'create_time']
    for p in psutil.process_iter(attrs):
        try:
            i = p.info
            cmd = " ".join(i['cmdline'] or [])[:80]
            if name_filter:
                needle = name_filter.lower()
                nm = (i['name'] or "").lower()
                if needle not in nm and needle not in cmd.lower():
                    continue
            running = int(time.time() - i['create_time'])
            observed = 0
            if window_mode:
                avg, observed = monitor.average(i['pid'], i['create_time'],
                                                avg_window_seconds)
                if avg is None:
                    continue                 # not watched yet, cannot judge
                cpu = avg
            else:
                cpu = i['cpu_percent'] or 0.0
            if cpu < min_cpu or running < min_running_seconds:
                continue
            row = {"pid": i['pid'], "name": i['name'],
                   "user": i['username'], "cmd": cmd,
                   "cpu_percent": round(cpu, 1),
                   "memory_percent": round(i['memory_percent'] or 0.0, 1),
                   "running_seconds": running}
            if window_mode:
                row["observed_seconds"] = int(observed)
            rows.append(row)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "memory_percent" if sort_by == "memory" else "cpu_percent"
    rows.sort(key=lambda r: r[key], reverse=True)
    rows = rows[:top_n]

    if window_mode:
        return {"window_seconds": avg_window_seconds,
                "monitor_running_seconds": monitor.running_seconds(),
                "note": ("cpu_percent is the AVERAGE over observed_seconds. If "
                         "observed_seconds is smaller than window_seconds, tell "
                         "the user the average covers only that time."),
                "processes": rows}
    return rows


def find_process_by_port(port):
    """Which process is listening on this network port? (is the port open?)"""
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        return "REFUSED: port must be a whole number from 1 to 65535."
    try:
        conns = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return "No permission to read network connections (try running as root)."
    pids, hidden = set(), False
    for c in conns:
        if c.laddr and c.laddr.port == port and c.status in (psutil.CONN_LISTEN,
                                                             psutil.CONN_NONE):
            if c.pid:
                pids.add(c.pid)
            else:
                hidden = True              # open, but the owner is another user
    procs = []
    for pid in sorted(pids):
        try:
            p = psutil.Process(pid)
            procs.append({"pid": pid, "name": p.name(), "user": p.username(),
                          "cmd": " ".join(p.cmdline())[:80]})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    result = {"port": port, "open": bool(procs) or hidden, "processes": procs}
    if hidden and not procs:
        result["note"] = "The port is open, but its process belongs to another user."
    return result


def _wait_until_gone(pid, timeout):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                return True
        except psutil.NoSuchProcess:
            return True
        time.sleep(0.1)
    return False


def send_signal(pid, sig="SIGTERM"):
    """Send a signal to a process, after safety checks."""
    problem = check_allowed(pid, sig)
    if problem:
        return problem
    try:
        os.kill(pid, getattr(signal, sig))
    except ProcessLookupError:
        return f"PID {pid} does not exist."
    except PermissionError:
        return f"No permission to signal PID {pid}."

    if sig in ("SIGTERM", "SIGKILL", "SIGINT", "SIGHUP"):
        if _wait_until_gone(pid, 3):
            return f"Sent {sig} to PID {pid}. The process has exited."
        return (f"Sent {sig} to PID {pid} but it is still running. "
                "Ask the user before escalating to SIGKILL.")
    return f"Sent {sig} to PID {pid}."


def renice_process(pid, nice_value):
    """Change priority. 19 = lowest priority, 0 = normal."""
    problem = check_allowed(pid)
    if problem:
        return problem
    if not -20 <= nice_value <= 19:
        return "REFUSED: nice value must be between -20 and 19."
    try:
        psutil.Process(pid).nice(nice_value)
        return f"PID {pid} priority set to {nice_value}."
    except psutil.AccessDenied:
        return "No permission (lowering the value below 0 needs root)."
    except psutil.NoSuchProcess:
        return f"PID {pid} does not exist."
