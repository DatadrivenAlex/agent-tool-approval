"""A bounded, typed tool router with explicit one-use approvals."""
from __future__ import annotations

import secrets
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class Decision:
    status: str
    result: object = None
    approval_id: str | None = None


@dataclass(frozen=True)
class Tool:
    handler: Callable[[dict], object]
    validate: Callable[[dict], None]
    requires_approval: bool = False


class ToolGate:
    """Demonstrates a gate; caller identity and approval must be authenticated externally."""

    def __init__(self, tools: dict[str, Tool]):
        self._tools = dict(tools)
        self._pending: dict[str, tuple[str, str, dict]] = {}
        self._lock = Lock()
        self.audit: list[dict] = []

    def request(self, actor: str, name: str, args: dict) -> Decision:
        if not actor or name not in self._tools:
            return Decision("denied")
        tool = self._tools[name]
        data = deepcopy(args)
        try:
            tool.validate(data)
        except (TypeError, ValueError, KeyError):
            return Decision("invalid")
        if tool.requires_approval:
            approval_id = secrets.token_urlsafe(24)
            with self._lock:
                self._pending[approval_id] = (actor, name, data)
                self.audit.append({"actor": actor, "tool": name, "event": "pending"})
            return Decision("approval_required", approval_id=approval_id)
        return self._run(actor, name, data)

    def approve(self, actor: str, approval_id: str) -> Decision:
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None or pending[0] != actor:
                return Decision("denied")
            del self._pending[approval_id]
        return self._run(*pending)

    def reject(self, actor: str, approval_id: str) -> Decision:
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None or pending[0] != actor:
                return Decision("denied")
            del self._pending[approval_id]
            self.audit.append({"actor": actor, "tool": pending[1], "event": "rejected"})
        return Decision("rejected")

    def _run(self, actor: str, name: str, args: dict) -> Decision:
        try:
            result = self._tools[name].handler(deepcopy(args))
        except Exception:  # noqa: BLE001 -- isolate errors from registered handlers
            with self._lock:
                self.audit.append({"actor": actor, "tool": name, "event": "failed"})
            return Decision("failed")
        with self._lock:
            self.audit.append({"actor": actor, "tool": name, "event": "executed"})
        return Decision("executed", result=result)
