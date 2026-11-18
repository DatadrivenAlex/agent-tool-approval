from concurrent.futures import ThreadPoolExecutor

import pytest

from toolgate.demo import make_gate
from toolgate.gate import Tool, ToolGate


def test_safe_tool_executes():
    d = make_gate().request("u", "add", {"a": 1, "b": 4})
    assert (d.status, d.result) == ("executed", 5)


@pytest.mark.parametrize("name", ["shell", "", "__import__"])
def test_unknown_tools_fail_closed(name):
    assert make_gate().request("u", name, {}).status == "denied"


@pytest.mark.parametrize("args", [{}, {"a": True, "b": 2}, {"a": 1, "b": 2, "x": 3}])
def test_invalid_add(args):
    assert make_gate().request("u", "add", args).status == "invalid"


def test_approval_exact_args_and_one_use():
    gate = make_gate()
    args = {"recipient": "Alice", "text": "hello"}
    d = gate.request("u", "simulate_message", args)
    args["text"] = "changed"
    assert gate.approve("u", d.approval_id).result["text"] == "hello"
    assert gate.approve("u", d.approval_id).status == "denied"


def test_another_actor_cannot_approve_or_consume():
    gate = make_gate()
    d = gate.request("a", "simulate_message", {"recipient": "b", "text": "x"})
    assert gate.approve("b", d.approval_id).status == "denied"
    assert gate.approve("a", d.approval_id).status == "executed"


def test_reject_prevents_execution():
    gate = make_gate()
    d = gate.request("a", "simulate_message", {"recipient": "b", "text": "x"})
    assert gate.reject("a", d.approval_id).status == "rejected"
    assert gate.approve("a", d.approval_id).status == "denied"


def test_approval_concurrent_only_once():
    gate = make_gate()
    d = gate.request("a", "simulate_message", {"recipient": "b", "text": "x"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(lambda _: gate.approve("a", d.approval_id).status, range(20)))
    assert statuses.count("executed") == 1


def test_failed_execution_consumes_approval():
    def bad(_):
        raise RuntimeError("failure")
    gate = ToolGate({"bad": Tool(bad, lambda _: None, True)})
    d = gate.request("a", "bad", {})
    assert gate.approve("a", d.approval_id).status == "failed"
    assert gate.approve("a", d.approval_id).status == "denied"
    assert gate.audit[-1]["event"] == "failed"


def test_no_actor():
    assert make_gate().request("", "add", {"a": 1, "b": 2}).status == "denied"
