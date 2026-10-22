"""EXAMPLE agent (read-only). Copy this folder to start a new agent."""
from agents.base import ToolAgent

from . import tools

TOOLS = [
    {"name": "get_disk_usage",
     "description": "Show total, used and free disk space for a folder path. Default is /.",
     "input_schema": {"type": "object",
                      "properties": {"path": {"type": "string", "description": "Folder path, default /."}},
                      "required": []}},
    {"name": "list_partitions",
     "description": "List all mounted disk partitions.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
]

AGENT = ToolAgent(
    name="disk_demo",
    description=("EXAMPLE agent for disk space: how full is the disk, "
                 "which partitions are mounted."),
    system_prompt=("You are the Disk Demo Agent inside an Ubuntu shell. "
                   "Use your tools to answer questions about disk space. "
                   "Keep answers short and clear."),
    tool_schemas=TOOLS,
    tool_functions={"get_disk_usage": tools.get_disk_usage,
                    "list_partitions": tools.list_partitions},
    needs_confirmation=set(),       # read-only tools need no approval
)
