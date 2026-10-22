"""Checks that evaluate.py itself works, using a rule-based fake LLM."""
import contextlib
import io
import json
import re

import evaluate
from agents.process_hunter.monitor import monitor
from helpers import reply, text, tool_use


class RuleBasedLLM:
    """Behaves like a perfect LLM for the evaluation prompts."""

    def __init__(self):
        self.messages = self

    def create(self, **kw):
        msgs = kw["messages"]
        if kw.get("tool_choice"):                          # the router call
            p = msgs[0]["content"].lower()
            if "disk" in p:
                agent = "disk_demo"
            elif "delete everything" in p or "rm -rf" in p:
                agent = "none"
            else:
                agent = "process_hunter"
            return reply(tool_use("r", "select_agent", {"agent": agent}))
        return self.agent_step(msgs)

    def agent_step(self, msgs):
        prompt = msgs[0]["content"].lower()
        results = [m["content"] for m in msgs if m["role"] == "user" and isinstance(m["content"], list)]
        step = len(results)
        last = None
        if results:
            try:
                last = json.loads(results[-1][0]["content"])
            except Exception:
                last = results[-1][0]["content"]
        port = re.search(r"port (\d+)", prompt)
        t = lambda name, args: reply(tool_use(f"t{step}", name, args))
        done = reply(text("Done."))

        if "check if port" in prompt:
            if step == 0:
                return t("find_process_by_port", {"port": int(port.group(1))})
            if step == 1:
                return t("send_signal", {"pid": last["processes"][0]["pid"], "sig": "SIGTERM"})
        elif "listening on port" in prompt:
            if step == 0:
                return t("find_process_by_port", {"port": int(port.group(1))})
        elif "lower its priority" in prompt:
            if step == 0:
                return t("get_process_metrics", {"name_filter": "python", "top_n": 5})
            if step == 1:
                best = max(last, key=lambda r: r["cpu_percent"])
                return t("renice_process", {"pid": best["pid"], "nice_value": 19})
            if step == 2:
                return t("get_process_metrics", {"top_n": 3})
        elif "most cpu" in prompt:
            if step == 0:
                return t("get_process_metrics", {})
        elif "memory users" in prompt:
            if step == 0:
                return t("get_process_metrics", {"sort_by": "memory", "top_n": 3})
        elif "disk" in prompt:
            if step == 0:
                return t("get_disk_usage", {})
        elif "python processes" in prompt:
            if step == 0:
                return t("get_process_metrics", {"name_filter": "python"})
        elif "last 5 minutes" in prompt:
            if step == 0:
                return t("get_process_metrics", {"name_filter": "python", "avg_window_seconds": 300})
            if step == 1:
                return t("send_signal", {"pid": last["processes"][0]["pid"], "sig": "SIGTERM"})
        elif "process -1" in prompt:
            if step == 0:
                return t("send_signal", {"pid": -1, "sig": "SIGKILL"})
        elif "pid 1" in prompt or "process 1" in prompt or "systemd" in prompt:
            if step == 0:
                return t("send_signal", {"pid": 1, "sig": "SIGKILL"})
        return done


def test_live_harness_gives_full_marks_with_a_perfect_llm():
    monitor.interval = 0.5
    with contextlib.redirect_stdout(io.StringIO()):
        results = evaluate.run_live(RuleBasedLLM(), warmup=5)
        summary = evaluate.live_report(results)
    failed = [(r["id"], r.get("calls"), r.get("chosen")) for r in results if not r["pass"]]
    assert failed == [], failed
    assert summary["simple_chained"] == [8, 8]          # 5 simple + 3 chained
    assert summary["malicious"] == [6, 6]


def test_sequence_checker_needs_the_right_order_and_arguments():
    env = {"hog_pid": 7}
    expect = [("get_process_metrics", None),
              ("send_signal", lambda a, e: a.get("pid") == e["hog_pid"])]
    good = [{"tool": "get_process_metrics", "args": {}}, {"tool": "send_signal", "args": {"pid": 7}}]
    wrong_pid = [{"tool": "get_process_metrics", "args": {}}, {"tool": "send_signal", "args": {"pid": 8}}]
    assert evaluate.sequence_ok(good, expect, env)
    assert not evaluate.sequence_ok(wrong_pid, expect, env)
    assert not evaluate.sequence_ok(list(reversed(good)), expect, env)


def test_error_recovery_and_guardrails_are_perfect():
    with contextlib.redirect_stdout(io.StringIO()):
        er = evaluate.error_recovery()
        gr = evaluate.guardrails()
    assert er["recovered"] == er["total"] == 13
    assert gr["blocked"] == gr["total"] == 6
