"""Tool-distribution and tool_choice policy.

Encodes two architectural decisions for the inventory agent:

* **Distribution** — the agent is scoped to four tools, within the 4-5-per-agent guideline
  (exam guide Task 2.3: too many tools, e.g. 18 vs 4-5, degrades selection reliability).
* **tool_choice** — each workflow maps to one of the three Messages API modes: forced single
  tool, ``any`` (must call a tool), or ``auto`` (model decides).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from mcp.server.fastmcp import FastMCP

from inventory_agent.bridge import anthropic_tool_schemas

MAX_TOOLS_PER_AGENT = 5
DEFAULT_MAX_TOKENS = 1024


class Workflow(StrEnum):
    """Retail workflows, each with a distinct tool_choice requirement."""

    VERIFY_BEFORE_RETURN = "verify_before_return"  # force check_stock first
    GUARANTEED_TOOL = "guaranteed_tool"  # any: must produce a structured tool call
    OPEN_ENDED = "open_ended"  # auto: model decides


def tool_choice_for(workflow: Workflow) -> dict[str, str]:
    """Return the Messages API ``tool_choice`` payload for a workflow."""
    # TODO: Map each workflow to its tool_choice payload. VERIFY_BEFORE_RETURN forces a single
    # named tool ({"type": "tool", "name": ...}) so sequencing is guaranteed; GUARANTEED_TOOL
    # uses {"type": "any"}; OPEN_ENDED uses {"type": "auto"}.
    raise NotImplementedError


def build_messages_request(
    model: str,
    messages: list[dict[str, Any]],
    server: FastMCP,
    workflow: Workflow,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, Any]:
    """Assemble a well-formed Anthropic Messages API request for a workflow."""
    # TODO: Assemble the request dict: model, max_tokens, messages, the scoped tool schemas
    # (from anthropic_tool_schemas), and the tool_choice for this workflow.
    raise NotImplementedError


class ReturnWorkflowGuard:
    """Enforces that ``check_stock`` is invoked before ``process_return``.

    Demonstrates forced-selection ordering at the application layer: the first turn forces
    ``check_stock`` (see ``Workflow.VERIFY_BEFORE_RETURN``), and this guard refuses a
    ``process_return`` until a stock check has been recorded.
    """

    def __init__(self) -> None:
        self._stock_checked = False

    def record(self, tool_name: str) -> None:
        # TODO: Remember when check_stock has run so the guard can release process_return.
        raise NotImplementedError

    def can_run(self, tool_name: str) -> bool:
        # TODO: Allow any tool except process_return, which is allowed only after check_stock
        # has been recorded.
        raise NotImplementedError
