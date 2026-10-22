import os
import shutil

import psutil


def get_disk_usage(path="/"):
    """Total, used and free space of the disk that holds `path`."""
    if not os.path.isdir(path):
        return f"'{path}' is not a directory."
    u = shutil.disk_usage(path)
    gb = 1024 ** 3
    return {"path": path, "total_gb": round(u.total / gb, 1),
            "used_gb": round(u.used / gb, 1), "free_gb": round(u.free / gb, 1),
            "used_percent": round(u.used / u.total * 100, 1)}


def list_partitions():
    """All mounted disk partitions."""
    return [{"device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype}
            for p in psutil.disk_partitions()]
