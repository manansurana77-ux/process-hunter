import subprocess
import sys
import time
from agents.process_hunter.tools import get_process_metrics, send_signal, renice_process


def start_hog():
    return subprocess.Popen([sys.executable, "-c", "while True: pass"])


def test_refuses_pid_1():
    assert "REFUSED" in send_signal(1, "SIGTERM")


def test_refuses_negative_pid():
    assert "REFUSED" in send_signal(-1, "SIGKILL")


def test_refuses_unknown_signal():
    hog = start_hog()
    try:
        assert "REFUSED" in send_signal(hog.pid, "SIGFOO")
    finally:
        hog.kill()
        hog.wait()


def test_missing_pid():
    assert "does not exist" in send_signal(999999, "SIGTERM")


def test_finds_cpu_hog():
    hog = start_hog()
    try:
        time.sleep(0.5)
        rows = get_process_metrics(top_n=5, name_filter="python")
        assert hog.pid in [r["pid"] for r in rows]
    finally:
        hog.kill()
        hog.wait()


def test_kills_cpu_hog():
    hog = start_hog()
    time.sleep(0.5)
    result = send_signal(hog.pid, "SIGTERM")
    hog.wait(timeout=5)
    assert "exited" in result
    assert hog.returncode is not None


def test_renice():
    hog = start_hog()
    try:
        assert "set to 10" in renice_process(hog.pid, 10)
    finally:
        hog.kill()
        hog.wait()
