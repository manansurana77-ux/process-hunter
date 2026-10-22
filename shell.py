"""The Base Shell: the master loop that sends each request to the right agent."""
import config
import router


class BaseShell:
    def __init__(self, agents, client=None, direct=None):
        self.agents = agents
        self._client = client
        self.direct = direct        # if set, skip the router and use this agent
        self.current = None

    def _get_client(self):
        if self._client is None:
            self._client = config.make_client()
        return self._client

    def start_agents(self):
        for agent in self.agents.values():
            try:
                agent.start()
            except Exception as e:
                print(f"[warning] agent '{agent.name}' failed to start: {e}")

    def handle_line(self, text):
        """One user sentence in, one answer out."""
        name = self.direct or router.choose_agent(
            self._get_client(), self.agents, text, self.current)
        if name is None:
            names = ", ".join(self.agents)
            return f"No agent can handle that yet. Available agents: {names}"
        self.current = name
        if not self.direct:
            print(f"[router] -> {name}")
        return self.agents[name].handle(text)

    def run(self):
        self.start_agents()
        mode = f"direct mode: {self.direct}" if self.direct else \
            f"{len(self.agents)} agent(s) loaded"
        print(f"Agentic AI Shell for Ubuntu ({mode})")
        print("Type a request in plain English. Commands: agents, reset, exit")
        while True:
            try:
                text = input("\nubuntu-ai> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                continue
            if text.lower() in ("exit", "quit"):
                break
            if text.lower() == "agents":
                for a in self.agents.values():
                    print(f"- {a.name}: {a.description}")
                continue
            if text.lower() == "reset":
                for a in self.agents.values():
                    if hasattr(a, "reset"):
                        a.reset()
                self.current = None
                print("Memory cleared.")
                continue
            try:
                print(self.handle_line(text))
            except Exception as e:
                print(f"Error: {e}")
