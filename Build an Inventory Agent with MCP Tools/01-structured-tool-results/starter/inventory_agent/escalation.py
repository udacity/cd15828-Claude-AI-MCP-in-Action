"""Structured escalation handoff.

When the agent halts on a permission error it must emit a compact, structured summary for a
human approver, not dump the raw transcript (Playbook *Escalation Handoff*).
"""

from __future__ import annotations

from pydantic import BaseModel


class Escalation(BaseModel):
    """Compact handoff payload produced when an action is blocked and needs human approval."""

    sku: str
    requested_change: str
    root_cause: str
    recommended_action: str


def build_escalation(sku: str, requested_change: str, root_cause: str) -> Escalation:
    """Build the escalation payload for a blocked, approval-gated action."""
    # TODO: Return a compact Escalation. Carry the sku, the requested change, the root cause, and
    # a recommended_action telling a human what to do next (route to a manager, then retry).
    raise NotImplementedError
