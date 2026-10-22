"""The Process Hunter Agent: ties the prompt, the tools and the safety together."""
from agents.base import ToolAgent

from . import tools
from .monitor import start_monitor
from .schemas import TOOLS

SYSTEM_PROMPT = """You are the Process Hunter Agent inside an Ubuntu shell.
You help the user find and manage running processes using your tools.
Rules:
- Always call get_process_metrics first to find the real PID. Never guess a PID.
- For requests like "for the last 5 minutes", call get_process_metrics with
  avg_window_seconds (5 minutes = 300). If observed_seconds is smaller than the
  window, tell the user the average covers only that time.
- To work with a network port, call find_process_by_port first and use the PID it
  returns. If the port is not open, say so and do not kill anything.
- If several processes match, list them and ask the user which one.
- Try SIGTERM before SIGKILL. Use SIGKILL only if the user agrees.
- If a tool says REFUSED, explain why in simple words. Do not try to get around it.
- Keep answers short and clear."""

AGENT = ToolAgent(
    name="process_hunter",
    description=("Finds, monitors, stops and re-prioritises running processes "
                 "(by CPU, memory, run time, name or network port). Use for requests like "
                 "'kill the python script using 90% CPU', 'which process uses "
                 "the most RAM', 'is port 8080 open, and kill it' or 'lower the "
                 "priority of ...'."),
    system_prompt=SYSTEM_PROMPT,
    tool_schemas=TOOLS,
    tool_functions={
        "get_process_metrics": tools.get_process_metrics,
        "find_process_by_port": tools.find_process_by_port,
        "send_signal": tools.send_signal,
        "renice_process": tools.renice_process,
    },
    needs_confirmation={"send_signal", "renice_process"},   # human y/n first
    on_start=start_monitor,
)
