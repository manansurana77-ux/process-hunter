"""Background CPU monitor: gives a real average CPU% over a time window.

psutil only measures CPU over short moments. To answer "for the last 5 minutes"
a small thread samples every process every few seconds and keeps the history.
"""
import threading
import time
from collections import deque

import psutil


class CpuMonitor:
    def __init__(self, interval=5.0, max_seconds=900):
        self.interval = interval
        self.max_seconds = max_seconds
        self._procs = {}            # (pid, start) -> [Process object, last time]
        self._samples = {}          # (pid, start) -> deque[(time, cpu, seconds)]
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self.started_at = None

    # --- control -----------------------------------------------------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self.started_at = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def running_seconds(self):
        return int(time.time() - self.started_at) if self.started_at else 0

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.sample_once()
            except Exception:
                pass
            self._stop.wait(self.interval)

    # --- sampling ----------------------------------------------------
    def sample_once(self):
        now = time.time()
        alive = set()
        with self._lock:
            for p in psutil.process_iter():
                try:
                    key = (p.pid, int(round(p.create_time())))
                    alive.add(key)
                    entry = self._procs.get(key)
                    if entry is None:
                        p.cpu_percent(None)          # first call only starts the counter
                        self._procs[key] = [p, now]
                        continue
                    proc, last = entry
                    cpu = proc.cpu_percent(None)     # CPU% since the previous call
                    seconds = now - last
                    entry[1] = now
                    if seconds > 0:
                        dq = self._samples.setdefault(key, deque())
                        dq.append((now, cpu, seconds))
                        while dq and dq[0][0] < now - self.max_seconds:
                            dq.popleft()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            for key in list(self._procs):            # forget processes that ended
                if key not in alive:
                    self._procs.pop(key, None)
                    self._samples.pop(key, None)

    # --- reading -----------------------------------------------------
    def average(self, pid, create_time, window_seconds):
        """Return (average CPU%, seconds actually observed) or (None, 0)."""
        key = (pid, int(round(create_time)))
        cutoff = time.time() - window_seconds
        with self._lock:
            used = [(c, s) for (t, c, s) in self._samples.get(key, ()) if t >= cutoff]
        total = sum(s for _, s in used)
        if total <= 0:
            return None, 0
        return sum(c * s for c, s in used) / total, total


monitor = CpuMonitor()


def start_monitor():
    monitor.start()
