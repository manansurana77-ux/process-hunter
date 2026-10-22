import os
import psutil

# Only these signals may ever be sent.
ALLOWED_SIGNALS = {"SIGTERM", "SIGKILL", "SIGSTOP", "SIGCONT", "SIGHUP", "SIGINT"}

# PID 0, PID 1 (systemd), this program, and the shell that started it.
PROTECTED_PIDS = {0, 1, os.getpid(), os.getppid()}

# Critical Ubuntu processes, protected by name.
PROTECTED_NAMES = {"systemd", "init", "sshd", "Xorg", "Xwayland",
                   "gnome-shell", "dbus-daemon", "NetworkManager", "gdm3"}


def check_allowed(pid, sig=None):
    """Return None if the action is OK, else a string saying why not."""
    if sig is not None and sig not in ALLOWED_SIGNALS:
        return f"REFUSED: signal {sig} is not allowed."
    if not isinstance(pid, int) or pid <= 1:
        return f"REFUSED: PID {pid} is invalid or protected."
    if pid in PROTECTED_PIDS:
        return f"REFUSED: PID {pid} is protected."
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        owner = proc.uids().real
    except psutil.NoSuchProcess:
        return f"PID {pid} does not exist."
    except psutil.AccessDenied:
        return f"REFUSED: no permission to inspect PID {pid}."
    if name in PROTECTED_NAMES:
        return f"REFUSED: '{name}' is a critical system process."
    if owner != os.getuid() and os.geteuid() != 0:
        return f"REFUSED: PID {pid} belongs to another user."
    return None
