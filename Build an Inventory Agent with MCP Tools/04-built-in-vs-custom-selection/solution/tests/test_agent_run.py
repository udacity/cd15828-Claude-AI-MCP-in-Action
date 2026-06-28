"""End-to-end agent run, CLI, escalation, and the MCP/API bridge.

Covers the committed real-API transcript structure, the CLI entry point,
structured escalation, plus the isError -> is_error bridge (validation C1).
"""

from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import pytest

from inventory_agent import __main__ as cli
from inventory_agent.bridge import to_tool_result_block
from inventory_agent.errors import ErrorCategory, ToolResult
from inventory_agent.escalation import build_escalation

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "demo_transcript.json"


@pytest.fixture
def events() -> list[dict[str, Any]]:
    return json.loads(FIXTURE.read_text())["events"]


# --- Transcript was real-API generated and has the expected structure -------


def test_transcript_contains_a_tool_invocation(events: list[dict[str, Any]]) -> None:
    assert any(e["type"] == "tool_use" for e in events)


def test_transcript_shows_transient_error_then_retry_recovery(events: list[dict[str, Any]]) -> None:
    transient_idx = next(
        i
        for i, e in enumerate(events)
        if e["type"] == "tool_result" and e.get("errorCategory") == "transient"
    )
    assert events[transient_idx]["isRetryable"] is True
    tool = events[transient_idx]["name"]
    # the same tool is retried and later succeeds
    recovered = any(
        e["type"] == "tool_result" and e["name"] == tool and e.get("isError") is False
        for e in events[transient_idx + 1 :]
    )
    assert recovered


def test_transcript_halts_on_permission_error_with_escalation(events: list[dict[str, Any]]) -> None:
    perm_idx = next(
        i
        for i, e in enumerate(events)
        if e["type"] == "tool_result" and e.get("errorCategory") == "permission"
    )
    assert events[perm_idx]["isRetryable"] is False
    # an escalation follows the permission failure, and it is the final event (halt)
    assert events[-1]["type"] == "escalation"
    assert any(e["type"] == "escalation" for e in events[perm_idx + 1 :])


# --- Structured escalation payload ------------------------------------------


def test_escalation_payload_has_required_fields(events: list[dict[str, Any]]) -> None:
    payload = next(e for e in events if e["type"] == "escalation")["payload"]
    assert set(payload) == {"sku", "requested_change", "root_cause", "recommended_action"}
    assert all(payload[k] for k in payload)


def test_build_escalation_shape() -> None:
    esc = build_escalation("SKU-1001", "update_price -> 69.99", "needs approval")
    dumped = esc.model_dump()
    assert dumped["sku"] == "SKU-1001"
    assert set(dumped) == {"sku", "requested_change", "root_cause", "recommended_action"}


# --- CLI entry point ---------------------------------------------------------


def test_console_script_is_registered() -> None:
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("retail-inventory-mcp-agent") == "inventory_agent.__main__:main"


def test_cli_replays_transcript_offline(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main()
    out = capsys.readouterr().out
    assert code == 0
    assert "check_stock" in out
    assert "ESCALATION" in out


# --- validation C1: MCP isError (camelCase) -> Messages API is_error (snake_case) ------


def test_tool_result_wire_uses_camelcase_iserror() -> None:
    wire = ToolResult.fail(ErrorCategory.TRANSIENT, "timeout").to_wire()
    assert "isError" in wire and "is_error" not in wire


def test_bridge_block_uses_snakecase_is_error() -> None:
    result = ToolResult.fail(ErrorCategory.PERMISSION, "denied")
    block = to_tool_result_block("tu_1", result)
    assert block["type"] == "tool_result"
    assert block["tool_use_id"] == "tu_1"
    assert block["is_error"] is True  # snake_case at the API boundary
    # the structured envelope (camelCase) is carried in the content payload
    assert json.loads(block["content"])["errorCategory"] == "permission"
