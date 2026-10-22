"""Start the Agentic AI Shell.

  python3 main.py                        base shell (router + all agents)
  python3 main.py --agent process_hunter talk to one agent directly
  python3 main.py --list                 show the loaded agents
"""
import argparse

import registry
from shell import BaseShell


def main():
    parser = argparse.ArgumentParser(description="Agentic AI Shell for Ubuntu")
    parser.add_argument("--agent", help="skip the router and use this agent")
    parser.add_argument("--list", action="store_true", help="list agents and exit")
    args = parser.parse_args()

    agents = registry.discover()
    if args.list:
        for a in agents.values():
            print(f"{a.name}: {a.description}")
        return
    if args.agent and args.agent not in agents:
        print(f"Unknown agent '{args.agent}'. Available: {', '.join(agents)}")
        return
    BaseShell(agents, direct=args.agent).run()


if __name__ == "__main__":
    main()
