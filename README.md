# Agent Tool Approval

An offline Python demonstration of a bounded tool router for AI agents. It routes only registered tools, validates arguments, and pauses simulated consequential actions for a one-use approval bound to the requester and an immutable snapshot of arguments.

## Workflow

1. A model proposes a tool name and arguments; the gateway checks the registry and validation.
2. Safe demo calculation runs immediately; `simulate_message` returns an approval token.
3. The same actor approves or rejects the exact request. A token can be consumed once, even under concurrent approvals.
4. A minimal in-memory audit records events without message text.

```bash
python -m pip install -e ".[dev]"
python -m toolgate.demo
pytest -q
ruff check .
```

## Scope and limitations

This is a local demo: no messages are sent and no LLM or external provider is called. Actor IDs are supplied by the caller, not authenticated; approvals and audit are in memory and disappear on restart. A real deployment needs authenticated identities, durable transactional storage, expiry, authorization, secret handling and proper observability. Never expose this demo as a security boundary or grant a model unrestricted tool access.
