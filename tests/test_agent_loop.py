import time

from agents.base import ToolAgent
from agents.process_hunter import AGENT
from agents.process_hunter.schemas import TOOLS
from helpers import FakeClient, reply, text, tool_use, start_hog


def make_agent(script, answer="y"):
    """The real Process Hunter agent, but with a fake LLM and a scripted user."""
    agent = ToolAgent(
        name=AGENT.name, description=AGENT.description,
        system_prompt=AGENT.system_prompt, tool_schemas=TOOLS,
        tool_functions=AGENT.tool_functions,
        needs_confirmation=AGENT.needs_confirmation,
        client=FakeClient(script), ask=lambda _: answer)
    return agent


def tool_results(agent):
    out = []
    for m in agent.history:
        if m["role"] == "user" and isinstance(m["content"], list):
            out += [r["content"] for r in m["content"]]
    return out


def test_full_kill_flow_with_fake_llm():
    hog = start_hog()
    time.sleep(0.5)
    agent = make_agent([
        reply(tool_use("t1", "get_process_metrics", {"name_filter": "python", "top_n": 5})),
        reply(tool_use("t2", "send_signal", {"pid": hog.pid, "sig": "SIGTERM"})),
        reply(text("I stopped the python process.")),
    ])
    answer = agent.handle("kill the python script using a lot of CPU")
    hog.wait(timeout=5)                           # it really died
    assert answer == "I stopped the python process."
    results = tool_results(agent)
    assert str(hog.pid) in results[0]             # LLM saw the real process table
    assert "has exited" in results[1]


def test_user_says_no_so_nothing_is_killed():
    hog = start_hog()
    try:
        agent = make_agent([
            reply(tool_use("t1", "send_signal", {"pid": hog.pid, "sig": "SIGTERM"})),
            reply(text("Okay, I did not stop it.")),
        ], answer="n")
        agent.handle("kill it")
        assert hog.poll() is None                 # still running
        assert "denied" in tool_results(agent)[0]
    finally:
        hog.kill()
        hog.wait()


def test_pid_1_is_refused_even_if_user_says_yes():
    agent = make_agent([
        reply(tool_use("t1", "send_signal", {"pid": 1, "sig": "SIGKILL"})),
        reply(text("That is a protected process.")),
    ])
    agent.handle("kill process 1")
    assert "REFUSED" in tool_results(agent)[0]


def test_unknown_tool_is_rejected():
    agent = make_agent([
        reply(tool_use("t1", "run_shell", {"cmd": "rm -rf /"})),
        reply(text("I cannot do that.")),
    ])
    agent.handle("delete everything")
    assert "Unknown tool" in tool_results(agent)[0]


def test_bad_arguments_become_a_message_not_a_crash():
    agent = make_agent([
        reply(tool_use("t1", "send_signal", {"wrong_name": 5})),
        reply(text("Sorry, that did not work.")),
    ])
    agent.handle("kill it")
    assert "Tool error" in tool_results(agent)[0]


def test_step_limit_stops_endless_loops():
    script = [reply(tool_use(f"t{i}", "renice_process", {"pid": 1, "nice_value": 5}))
              for i in range(20)]
    agent = make_agent(script)
    assert agent.handle("loop forever").startswith("Stopped")


def test_tool_schemas_match_tool_functions():
    names = {t["name"] for t in TOOLS}
    assert names == set(AGENT.tool_functions)
