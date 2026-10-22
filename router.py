"""The LLM router: reads the user sentence and picks ONE agent."""
import config


def choose_agent(client, agents, user_text, current=None):
    """Return the chosen agent name, or None if no agent fits."""
    names = list(agents) + ["none"]
    catalog = "\n".join(f"- {n}: {a.description}" for n, a in agents.items())
    system = (
        "You are the router of an agentic Ubuntu shell. Choose exactly one "
        "agent for the user's request, using select_agent.\n"
        "Available agents:\n" + catalog + "\n"
        "Use 'none' only if no agent fits.")
    if current:
        system += (f" The previous request was handled by '{current}'. "
                   "Keep it for follow-up messages such as 'kill it'.")
    tool = {
        "name": "select_agent",
        "description": "Pick the agent that should handle the user's request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": names},
                "reason": {"type": "string", "description": "One short sentence."},
            },
            "required": ["agent"],
        },
    }
    response = client.messages.create(
        model=config.MODEL, max_tokens=200, system=system, tools=[tool],
        tool_choice={"type": "tool", "name": "select_agent"},
        messages=[{"role": "user", "content": user_text}])
    for block in response.content:
        if block.type == "tool_use" and block.name == "select_agent":
            choice = block.input.get("agent")
            return choice if choice in agents else None
    return None
