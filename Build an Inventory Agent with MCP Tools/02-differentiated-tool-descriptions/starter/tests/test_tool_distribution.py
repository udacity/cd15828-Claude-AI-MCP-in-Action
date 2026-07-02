"""Tool distribution and tool_choice configuration.

Covers exactly four scoped tools, tool_choice payloads,
the check_stock-before-process_return sequence guard, and well-formed
Anthropic Messages request payloads.
"""

from __future__ import annotations

import pytest

from inventory_agent.bridge import anthropic_tool_schemas
from inventory_agent.policy import (
    MAX_TOOLS_PER_AGENT,
    ReturnWorkflowGuard,
    Workflow,
    build_messages_request,
    tool_choice_for,
)
from inventory_agent.server import EXPECTED_TOOLS, build_server

# --- Tool scope and schema shape -------------------------------------------------------------------------


def test_agent_is_configured_with_exactly_four_tools() -> None:
    schemas = anthropic_tool_schemas(build_server())
    names = {s["name"] for s in schemas}
    assert names == EXPECTED_TOOLS
    assert len(schemas) == 4
    assert len(schemas) <= MAX_TOOLS_PER_AGENT  # 4-5 per-agent guideline


def test_no_out_of_scope_tool_leaks_into_the_schema_list() -> None:
    names = {s["name"] for s in anthropic_tool_schemas(build_server())}
    assert not (names - EXPECTED_TOOLS)


def test_each_anthropic_schema_is_well_formed() -> None:
    for s in anthropic_tool_schemas(build_server()):
        assert s["name"] and s["description"]
        assert s["input_schema"]["type"] == "object"
        assert s["input_schema"]["properties"]


# --- tool_choice payloads -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "workflow,expected",
    [
        (Workflow.VERIFY_BEFORE_RETURN, {"type": "tool", "name": "check_stock"}),
        (Workflow.GUARANTEED_TOOL, {"type": "any"}),
        (Workflow.OPEN_ENDED, {"type": "auto"}),
    ],
)
def test_tool_choice_payload_per_workflow(workflow: Workflow, expected: dict[str, str]) -> None:
    assert tool_choice_for(workflow) == expected


# --- Return-workflow sequence guard -------------------------------------------------------------------------


def test_return_guard_blocks_process_return_before_check_stock() -> None:
    guard = ReturnWorkflowGuard()
    assert guard.can_run("process_return") is False
    assert guard.can_run("check_stock") is True  # unrelated tools are unaffected


def test_return_guard_allows_process_return_after_check_stock() -> None:
    guard = ReturnWorkflowGuard()
    guard.record("check_stock")
    assert guard.can_run("process_return") is True


def test_verify_before_return_workflow_forces_check_stock_first() -> None:
    assert tool_choice_for(Workflow.VERIFY_BEFORE_RETURN) == {"type": "tool", "name": "check_stock"}


# --- Messages request payloads -------------------------------------------------------------------------


def test_request_payload_carries_tools_and_messages() -> None:
    messages = [{"role": "user", "content": "how many SKU-1001 in the east warehouse?"}]
    req = build_messages_request("claude-haiku-4-5-20251001", messages, build_server(), Workflow.OPEN_ENDED)
    assert req["model"] == "claude-haiku-4-5-20251001"
    assert req["messages"] == messages
    assert isinstance(req["max_tokens"], int) and req["max_tokens"] > 0
    assert len(req["tools"]) == 4
    assert all("input_schema" in t for t in req["tools"])


@pytest.mark.parametrize(
    "workflow,expected",
    [
        (Workflow.VERIFY_BEFORE_RETURN, {"type": "tool", "name": "check_stock"}),
        (Workflow.GUARANTEED_TOOL, {"type": "any"}),
        (Workflow.OPEN_ENDED, {"type": "auto"}),
    ],
)
def test_request_payload_tool_choice_matches_workflow(
    workflow: Workflow, expected: dict[str, str]
) -> None:
    req = build_messages_request("claude-haiku-4-5-20251001", [], build_server(), workflow)
    assert req["tool_choice"] == expected
