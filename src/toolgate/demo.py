"""Run an entirely offline agent-tool approval example."""
from toolgate.gate import Tool, ToolGate


def validate_add(args):
    if set(args) != {"a", "b"} or any(type(args[k]) is not int for k in args):
        raise ValueError("expected integer a and b")


def validate_message(args):
    if set(args) != {"recipient", "text"}:
        raise ValueError("expected recipient and text")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in args.values()):
        raise ValueError("text fields must be nonempty and at most 500 characters")


def make_gate():
    return ToolGate({
        "add": Tool(lambda x: x["a"] + x["b"], validate_add),
        "simulate_message": Tool(
            lambda x: {"simulated": True, **x}, validate_message, requires_approval=True
        ),
    })


def main():
    gate = make_gate()
    print("read-only:", gate.request("alex", "add", {"a": 2, "b": 3}))
    decision = gate.request("alex", "simulate_message", {"recipient": "demo", "text": "Hello"})
    print("before approval:", decision.status)
    print("after approval:", gate.approve("alex", decision.approval_id))
    print("events:", gate.audit)


if __name__ == "__main__":
    main()
