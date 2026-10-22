"""The contract every agent follows, plus a ready-made LLM tool-calling agent."""
import json

import config


class Agent:
    """What the Base Shell expects from every agent."""
    name = "agent"                      # short unique id, e.g. "process_hunter"
    description = "what this agent does"  # the router reads this to choose

    def start(self):
        """Optional: called once when the shell starts."""

    def handle(self, user_text):
        """Take one user sentence, return one English answer."""
        raise NotImplementedError


class ToolAgent(Agent):
    """An agent driven by LLM function calling.

    You give it a system prompt, tool descriptions (JSON schemas) and the real
    Python functions. It runs the loop: ask LLM -> run tool -> send result back.
    """

    def __init__(self, name, description, system_prompt, tool_schemas,
                 tool_functions, needs_confirmation=(), on_start=None,
                 client=None, ask=input):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tool_schemas = tool_schemas
        self.tool_functions = tool_functions
        self.needs_confirmation = set(needs_confirmation)
        self._on_start = on_start
        self._client = client
        self._ask = ask
        self.history = []

    # --- helpers -----------------------------------------------------
    def _get_client(self):
        if self._client is None:
            self._client = config.make_client()
        return self._client

    def start(self):
        if self._on_start:
            self._on_start()

    def reset(self):
        self.history.clear()

    def run_tool(self, name, args):
        """Run one tool the LLM asked for (with human confirmation if needed)."""
        func = self.tool_functions.get(name)
        if func is None:
            return f"Unknown tool: {name}"
        if name in self.needs_confirmation:
            print(f"\n[{self.name} wants to run] {name}({args})")
            if self._ask("Allow? (y/n): ").strip().lower() != "y":
                return "The user denied this action."
        try:
            result = func(**args)
        except Exception as e:
            return f"Tool error: {e}"
        return result if isinstance(result, str) else json.dumps(result)

    # --- the agent loop ----------------------------------------------
    def handle(self, user_text):
        history = self.history
        history.append({"role": "user", "content": user_text})
        try:
            for _ in range(config.MAX_STEPS):
                response = self._get_client().messages.create(
                    model=config.MODEL, max_tokens=1024,
                    system=self.system_prompt, tools=self.tool_schemas,
                    messages=history)
                history.append({"role": "assistant", "content": response.content})

                # No tool requested -> this is the final answer.
                if response.stop_reason != "tool_use":
                    return "".join(b.text for b in response.content
                                   if b.type == "text")

                # Run every tool the LLM asked for and send the results back.
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"[tool] {block.name}({block.input})")
                        output = self.run_tool(block.name, block.input)
                        results.append({"type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": output})
                history.append({"role": "user", "content": results})
        except Exception:
            history.clear()   # never keep a half-finished conversation
            raise
        return "Stopped: too many steps without a final answer."
