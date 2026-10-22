TOOLS = [
    {
        "name": "get_process_metrics",
        "description": (
            "List running processes with PID, name, command line, CPU%, "
            "RAM% and how long they have been running. Use this first to "
            "find the right PID. Sorted highest first."),
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer",
                          "description": "How many processes to return. Default 10."},
                "name_filter": {"type": "string",
                                "description": "Keep only processes whose name or "
                                               "command contains this text."},
                "min_cpu": {"type": "number",
                            "description": "Keep only processes using at least "
                                           "this CPU percent."},
                "min_running_seconds": {"type": "integer",
                                        "description": "Keep only processes running at "
                                                       "least this many seconds."},
                "sort_by": {"type": "string", "enum": ["cpu", "memory"],
                            "description": "Sort by CPU or memory. Default cpu."},
                "avg_window_seconds": {"type": "integer",
                                       "description": "Use the AVERAGE CPU over this many "
                                                      "seconds, for example 300 for the last "
                                                      "5 minutes. Result then also reports how "
                                                      "long the monitor has been watching."},
            },
            "required": [],
        },
    },
    {
        "name": "find_process_by_port",
        "description": (
            "Find which process is listening on a network port. Use it to "
            "check if a port (for example 8080) is open and to get the PID "
            "of the process that uses it."),
        "input_schema": {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "description": "Port number, 1 to 65535."},
            },
            "required": ["port"],
        },
    },
    {
        "name": "send_signal",
        "description": (
            "Send a signal to a process by PID. SIGTERM asks it to stop "
            "politely, SIGKILL forces it, SIGSTOP pauses it, SIGCONT resumes it. "
            "Always try SIGTERM before SIGKILL."),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Process ID."},
                "sig": {"type": "string",
                        "enum": ["SIGTERM", "SIGKILL", "SIGSTOP", "SIGCONT",
                                 "SIGHUP", "SIGINT"]},
            },
            "required": ["pid", "sig"],
        },
    },
    {
        "name": "renice_process",
        "description": (
            "Change the priority of a process without killing it. "
            "nice_value 19 is lowest priority, 0 is normal."),
        "input_schema": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer"},
                "nice_value": {"type": "integer",
                               "description": "Between -20 and 19."},
            },
            "required": ["pid", "nice_value"],
        },
    },
]
