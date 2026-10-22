import registry
import router
from agents.base import ToolAgent
from shell import BaseShell
from helpers import FakeClient, reply, text, tool_use


def test_registry_finds_both_agents():
    found = registry.discover()
    assert "process_hunter" in found and "disk_demo" in found


def test_router_forces_the_select_agent_tool_and_returns_name():
    agents = registry.discover()
    client = FakeClient([reply(tool_use("r1", "select_agent", {"agent": "process_hunter"}))])
    assert router.choose_agent(client, agents, "kill python") == "process_hunter"
    call = client.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "select_agent"}
    assert "process_hunter" in call["system"] and "disk_demo" in call["system"]


def test_router_none_and_invalid_names_give_none():
    agents = registry.discover()
    for choice in ("none", "made_up_agent"):
        client = FakeClient([reply(tool_use("r1", "select_agent", {"agent": choice}))])
        assert router.choose_agent(client, agents, "hello") is None


def test_router_remembers_previous_agent_for_follow_ups():
    agents = registry.discover()
    client = FakeClient([reply(tool_use("r1", "select_agent", {"agent": "process_hunter"}))])
    router.choose_agent(client, agents, "kill it", current="process_hunter")
    assert "previous request was handled by 'process_hunter'" in client.calls[0]["system"]


def test_shell_routes_then_agent_uses_its_tool():
    agents = registry.discover()
    llm = FakeClient([
        reply(tool_use("r1", "select_agent", {"agent": "disk_demo"})),            # router
        reply(tool_use("d1", "get_disk_usage", {"path": "/"})),                   # agent asks tool
        reply(text("The disk is fine.")),                                         # agent answers
    ])
    disk = agents["disk_demo"]
    disk._client = llm
    shell = BaseShell(agents, client=llm)
    try:
        assert shell.handle_line("how full is my disk?") == "The disk is fine."
        assert shell.current == "disk_demo"
        tool_result = disk.history[-2]["content"][0]["content"]
        assert "total_gb" in tool_result
    finally:
        disk._client = None
        disk.reset()


def test_shell_says_so_when_no_agent_fits():
    agents = registry.discover()
    llm = FakeClient([reply(tool_use("r1", "select_agent", {"agent": "none"}))])
    out = BaseShell(agents, client=llm).handle_line("book me a flight")
    assert out.startswith("No agent can handle that yet")


def test_direct_mode_skips_the_router():
    agents = registry.discover()
    llm = FakeClient([reply(text("Hello from disk agent."))])    # only ONE scripted reply
    disk = agents["disk_demo"]
    disk._client = llm
    try:
        shell = BaseShell(agents, client=llm, direct="disk_demo")
        assert shell.handle_line("hi") == "Hello from disk agent."
        assert len(llm.calls) == 1                               # no router call
    finally:
        disk._client = None
        disk.reset()
