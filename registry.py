"""Finds every agent inside the agents/ folder automatically."""
import importlib
import pkgutil

import agents


def discover():
    """Return {agent_name: agent_object} for every folder that defines AGENT."""
    found = {}
    for m in pkgutil.iter_modules(agents.__path__):
        if not m.ispkg or m.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"agents.{m.name}")
            agent = module.AGENT
            found[agent.name] = agent
        except Exception as e:           # one broken agent must not stop the shell
            print(f"[warning] could not load agent '{m.name}': {e}")
    return found
