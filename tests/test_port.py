import socket
import subprocess
import sys
import time

from agents.process_hunter.tools import find_process_by_port


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_finds_the_process_listening_on_a_port():
    port = free_port()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(port),
                               "--bind", "127.0.0.1"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        result = None
        for _ in range(50):                      # wait until the server is up
            result = find_process_by_port(port)
            if result["open"]:
                break
            time.sleep(0.1)
        assert result["open"] is True
        assert server.pid in [p["pid"] for p in result["processes"]]
    finally:
        server.kill()
        server.wait()


def test_closed_port_is_reported_closed():
    result = find_process_by_port(free_port())
    assert result["open"] is False and result["processes"] == []


def test_invalid_port_is_refused():
    for bad in ("abc", 0, 70000, -5, None, True):
        assert "REFUSED" in find_process_by_port(bad)
