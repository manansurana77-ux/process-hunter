# Adding a new agent (for the other pairs)

1. Copy the example folder:
   ```bash
   cp -r agents/disk_demo agents/my_agent
   ```
2. Edit `agents/my_agent/tools.py`: write your real Python functions.
3. Edit `agents/my_agent/agent.py`:
   - `TOOLS`: one description (name, what it does, inputs) per function
   - `name`: short unique id, for example `network_agent`
   - `description`: the router reads this to decide when to use your agent,
     so describe clearly what requests it should get
   - `system_prompt`: the rules for the LLM
   - `needs_confirmation`: put the names of tools that CHANGE the system here
     (the user must type y first)
4. Keep `agents/my_agent/__init__.py` as: `from .agent import AGENT`
5. Check it loads: `python3 main.py --list`
6. Test it alone: `python3 main.py --agent my_agent`
7. Add tests in `tests/` (see `tests/test_agent_loop.py` for a fake-LLM example).

Rules for safe tools: validate every input, never run text as a shell command,
return plain text or a dict, and put dangerous actions behind `needs_confirmation`.
