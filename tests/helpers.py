"""Small fake LLM so the agent loop can be tested without an API key."""
import subprocess
import sys
from types import SimpleNamespace


def text(t):
    return SimpleNamespace(type="text", text=t)


def tool_use(id_, name, input_):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


def reply(*blocks):
    stop = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return SimpleNamespace(content=list(blocks), stop_reason=stop)


class FakeClient:
    """Returns the scripted replies one by one and records every call."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.messages = self          # so client.messages.create(...) works

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.script.pop(0)


def start_hog():
    return subprocess.Popen([sys.executable, "-c", "while True: pass"])
