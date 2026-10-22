# Agentic AI Shell for Ubuntu: Process Hunter Agent

Type plain English in the terminal. An LLM (Claude) understands the request,
and our Python code runs safe Linux actions.

```
You:  Kill the python script that has been using 90% CPU for the last 5 minutes
 |
 v
Base Shell (shell.py)  --asks the LLM router (router.py)-->  picks ONE agent
 |
 v
Process Hunter Agent (agents/process_hunter)
 |   LLM picks a tool -> y/n question -> safety.py checks -> real action
 v
Ubuntu / Linux kernel (psutil, os.kill)
```

The LLM never touches the system. It only asks for a tool. Our code checks it.

## Folder structure

```
process_hunter_agent/
|-- main.py              start the shell (router + all agents)
|-- shell.py             Base Shell: the master loop
|-- router.py            LLM router: chooses the agent
|-- registry.py          finds every agent in agents/ automatically
|-- config.py            model name, step limit, API client
|-- agents/
|   |-- base.py          Agent contract + ToolAgent (the LLM tool loop)
|   |-- process_hunter/  OUR AGENT
|   |   |-- agent.py       prompt + tool wiring
|   |   |-- tools.py       4 tools: get_process_metrics, find_process_by_port, send_signal, renice_process
|   |   |-- schemas.py     tool descriptions for the LLM
|   |   |-- safety.py      the guard (protected PIDs, signals, owner)
|   |   |-- monitor.py     background CPU monitor ("last 5 minutes")
|   |-- disk_demo/       EXAMPLE agent, template for other pairs
|-- evaluate.py          measures accuracy, latency, error recovery (Chapter 5)
|-- tests/               30 automatic tests (no API key needed)
|-- docs/                ADDING_AN_AGENT.md, STEP_BY_STEP.md
|-- requirements.txt
```

## Requirements

- Ubuntu / Linux (uses Linux signals and /proc, so not plain Windows)
- Python 3.10 or newer
- An Anthropic API key (only for talking to the LLM; tests do not need it)

## Setup

```bash
cd process_hunter_agent
sudo apt install python3-venv -y        # only if venv fails
python3 -m venv venv
source venv/bin/activate                # repeat in EVERY new terminal
pip install -r requirements.txt
```

## Run the tests (no API key)

```bash
python3 -m pytest tests -v
```

Expected: `30 passed`.

## Run the shell

```bash
export ANTHROPIC_API_KEY="paste-your-key-here"    # repeat in every new terminal
python3 main.py                                   # base shell with router
python3 main.py --agent process_hunter            # talk to our agent directly
python3 main.py --list                            # show loaded agents
```

Shell commands: `agents` (list), `reset` (clear memory), `exit`.

### Demo prompts

First start a fake CPU hog in another terminal: `python3 -c "while True: pass"`

1. `Which processes are using the most CPU?`
2. `Show me the top 3 memory users`
3. `Kill the python script that has been using a lot of CPU for the last 5 minutes`
   (answer `y` when asked "Allow?")
4. `Kill process 1`   (safety refuses)
5. `Slow down the python hog instead of killing it`
6. `Check if port 8080 is open, and if it is, kill the process`  (first run `python3 -m http.server 8080` in another terminal)
7. `How full is my disk?`   (routed to the example disk agent)

## Evaluation (Chapter 5)

```bash
python3 evaluate.py            # offline: error recovery, guardrails, tool latency (no key)
python3 evaluate.py --live     # also: LLM intent accuracy + latency, in DRY-RUN mode
```

Dry-run means the real safety checks run but nothing is killed. Results are also
saved to `evaluation_results.json`.

## The "last 5 minutes" feature

A background monitor (`monitor.py`) samples every process every 5 seconds from
the moment the shell starts. For "the last 5 minutes" the agent asks for the
AVERAGE CPU over 300 seconds. If the shell has only been running for 40 seconds,
the result says so (`observed_seconds`) and the agent tells you the average
covers only that time. Start the shell, wait, then ask.

## Safety design

- The LLM can only call fixed tools. There is no "run any command" tool.
- Signal whitelist, protected PIDs (0, 1, the agent, its parent shell),
  protected program names, owner check, PID must be greater than 1.
- Human confirmation (y/n) before any kill or priority change.
- SIGTERM before SIGKILL. 8-step limit per request.
- The API key is read from an environment variable, never stored in code.

## Add another agent

See `docs/ADDING_AN_AGENT.md`. Copy `agents/disk_demo`, change the name,
description and tools. The shell finds it automatically.

## Teamwork rules (GitHub)

- `git pull` before you start. Commit small changes, then `git push`.
- Each person works on their own agent folder to avoid conflicts.
- Never commit your API key (`.gitignore` blocks `.env` and `venv/`).
