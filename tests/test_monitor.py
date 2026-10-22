import time

from agents.process_hunter.monitor import CpuMonitor
from agents.process_hunter import tools
from helpers import start_hog


def test_monitor_measures_average_cpu_of_a_hog():
    mon = CpuMonitor(interval=0.5)
    hog = start_hog()
    try:
        mon.start()
        time.sleep(3.2)
        import psutil
        ct = psutil.Process(hog.pid).create_time()
        avg, observed = mon.average(hog.pid, ct, 300)
        assert avg is not None and avg > 50       # a busy loop uses ~100% of a core
        assert observed >= 2                       # it really watched for a while
    finally:
        mon.stop()
        hog.kill()
        hog.wait()


def test_monitor_unknown_process_has_no_average():
    mon = CpuMonitor(interval=0.5)
    avg, observed = mon.average(999999, 0, 300)
    assert avg is None and observed == 0


def test_window_mode_returns_average_and_honest_note(monkeypatch):
    fast = CpuMonitor(interval=0.5)
    monkeypatch.setattr(tools, "monitor", fast)
    monkeypatch.setattr(tools, "start_monitor", fast.start)
    hog = start_hog()
    try:
        fast.start()
        time.sleep(3.2)
        result = tools.get_process_metrics(top_n=5, name_filter="python",
                                           avg_window_seconds=300)
        assert result["window_seconds"] == 300
        assert "AVERAGE" in result["note"]
        rows = {r["pid"]: r for r in result["processes"]}
        assert hog.pid in rows
        assert rows[hog.pid]["observed_seconds"] < 300     # honest: only ~3 s watched
        assert rows[hog.pid]["cpu_percent"] > 50
    finally:
        fast.stop()
        hog.kill()
        hog.wait()
