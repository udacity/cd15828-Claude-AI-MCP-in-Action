"""The **audit trail** (enterprise decision #4) and the **gateway** every governed tool
call passes through (decision #3).

Every MCP tool call routed through :class:`AuditedToolRunner` produces exactly one
append-only :class:`AuditEntry` carrying the *scope* (the identity boundary), the server,
the tool, the caller, an argument **digest** (never raw PII/credentials), and the outcome.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, ConfigDict

from mcp_governance.scoping import Scope

if TYPE_CHECKING:
    from mcp_governance.bridge import Bridge


class Clock(Protocol):
    """Injected so audit timestamps are deterministic in tests."""

    def now(self) -> str: ...


class SystemClock:
    def now(self) -> str:
        return datetime.now(UTC).isoformat()


class FixedClock:
    """Monotonic, deterministic clock for tests."""

    def __init__(self, start: int = 0) -> None:
        self._t = start

    def now(self) -> str:
        value = f"1970-01-01T00:00:{self._t:02d}+00:00"
        self._t += 1
        return value


def arg_digest(args: dict[str, Any]) -> str:
    """A stable SHA-256 digest of tool arguments. Identical args -> identical digest;
    raw values (e.g. a claim_id) never appear in cleartext in the audit entry."""
    # TODO (LO-6 audit trail): return a stable SHA-256 hex digest of `args` so identical
    #   args produce an identical digest and a raw claim_id/policy_id NEVER lands in the
    #   trail in cleartext. Hash a canonical JSON encoding (sort_keys=True, compact
    #   separators, default=str) so dict ordering doesn't change the digest.
    raise NotImplementedError


class AuditEntry(BaseModel):
    """One immutable audit record."""

    model_config = ConfigDict(frozen=True)

    timestamp: str
    server: str
    scope: Scope
    tool: str
    caller_identity: str
    arg_digest: str
    outcome: str  # "ok" | "error"


class AuditTrail:
    """Append-only, inspectable log. There is no public mutate or delete API."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        # TODO (LO-6 audit trail): append `entry`. The trail is APPEND-ONLY -- this is the
        #   only way entries enter it, and there is deliberately no mutate/delete API, so a
        #   compliance log can never be quietly edited after the fact.
        raise NotImplementedError

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def to_json(self) -> str:
        return json.dumps([e.model_dump() for e in self._entries], indent=2)

    def append_to_file(self, path: Path) -> None:
        """Persist the trail for later compliance review (JSON array on disk)."""
        existing: list[dict[str, Any]] = []
        if path.exists():
            existing = json.loads(path.read_text())
        existing.extend(e.model_dump() for e in self._entries)
        path.write_text(json.dumps(existing, indent=2))

    @staticmethod
    def load_file(path: Path) -> list[AuditEntry]:
        if not path.exists():
            return []
        return [AuditEntry.model_validate(r) for r in json.loads(path.read_text())]


class AuditedToolRunner:
    """The gateway: dispatch a tool call and record exactly one audit entry for it."""

    def __init__(
        self,
        bridge: Bridge,
        trail: AuditTrail,
        clock: Clock | None = None,
        caller_identity: str = "unknown",
    ) -> None:
        self._bridge = bridge
        self._trail = trail
        self._clock = clock or SystemClock()
        self._caller = caller_identity

    def run(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        # TODO (LO-6 gateway): EVERY governed tool call passes through here. Steps:
        #   1. digest = arg_digest(args)  (never store raw args)
        #   2. resolve server + scope from the bridge (server_for / scope_for)
        #   3. dispatch the call via self._bridge.dispatch(name, args); outcome is "error"
        #      if result.get("is_error") else "ok"
        #   4. CATCH any exception into a structured error result (never let a tool crash
        #      the loop -- Graceful Tool Failure), outcome "error"
        #   5. record EXACTLY ONE AuditEntry (timestamp from self._clock.now(), the scope as
        #      the identity boundary, the digest, the caller, the outcome)
        #   6. return the result dict
        raise NotImplementedError
