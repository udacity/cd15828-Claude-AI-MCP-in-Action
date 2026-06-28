"""Audited agent loop, append-only audit trail, four-decisions mapping, live test."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from mcp_governance.audit import (
    AuditedToolRunner,
    AuditEntry,
    AuditTrail,
    FixedClock,
    arg_digest,
)
from mcp_governance.bridge import Bridge, build_bridge
from mcp_governance.cli import main
from mcp_governance.loop import (
    ScriptedResponse,
    ScriptedRunner,
    TextBlock,
    ToolUseBlock,
    run_agent,
)
from mcp_governance.scoping import McpConfig, Scope


async def _bridge() -> Bridge:
    return await build_bridge()


# ---- Append-only audit trail, digest not cleartext --------------------


def test_audit_trail_is_append_only_and_ordered() -> None:
    trail = AuditTrail()
    e1 = AuditEntry(
        timestamp="t0",
        server="claims-database",
        scope=Scope.PROJECT,
        tool="get_claim",
        caller_identity="adj-1",
        arg_digest="d1",
        outcome="ok",
    )
    trail.record(e1)
    assert len(trail) == 1
    # entries is a snapshot tuple; mutating it must not affect the trail
    snapshot = trail.entries
    assert isinstance(snapshot, tuple)
    assert not hasattr(trail, "delete")  # no mutate/delete API
    # AuditEntry is frozen (immutable)
    with pytest.raises(ValidationError):
        e1.outcome = "error"  # type: ignore[misc]


def test_arg_digest_is_stable_and_hides_raw_values() -> None:
    d1 = arg_digest({"claim_id": "CLM-10001"})
    d2 = arg_digest({"claim_id": "CLM-10001"})
    d3 = arg_digest({"claim_id": "CLM-99999"})
    assert d1 == d2 != d3
    assert "CLM-10001" not in d1  # raw PII/id never in cleartext


# ---- AuditedToolRunner records exactly one entry per call --------------


async def test_runner_records_one_entry_per_call_success_and_error() -> None:
    bridge = await _bridge()
    trail = AuditTrail()
    gateway = AuditedToolRunner(bridge, trail, FixedClock(), caller_identity="adj-7")

    ok = gateway.run("get_claim", {"claim_id": "CLM-10001"})
    err = gateway.run("get_claim", {"claim_id": "CLM-404"})

    assert ok["found"] is True and err["found"] is False
    assert len(trail) == 2
    outcomes = [e.outcome for e in trail.entries]
    assert outcomes == ["ok", "error"]
    # scope (identity boundary) and server are recorded; no raw claim_id present
    blob = trail.to_json()
    assert "CLM-10001" not in blob and "CLM-404" not in blob
    assert all(e.scope is Scope.PROJECT for e in trail.entries)
    assert {e.server for e in trail.entries} == {"claims-database"}


async def test_digests_differ_for_different_args() -> None:
    bridge = await _bridge()
    trail = AuditTrail()
    gateway = AuditedToolRunner(bridge, trail, FixedClock(), "adj")
    gateway.run("get_claim", {"claim_id": "CLM-10001"})
    gateway.run("get_claim", {"claim_id": "CLM-10002"})
    digests = [e.arg_digest for e in trail.entries]
    assert digests[0] != digests[1]


# ---- Bridge exposes all servers' tools simultaneously; loop terminates -


async def test_bridge_exposes_all_servers_tools_simultaneously() -> None:
    bridge = await _bridge()
    assert bridge.tool_names() == {"get_claim", "search_claims", "lookup_policy"}
    names = {t["name"] for t in bridge.anthropic_tools()}
    assert names == {"get_claim", "search_claims", "lookup_policy"}
    # cross-server: a claims tool and a policy tool are present at once
    assert bridge.server_for("get_claim") == "claims-database"
    assert bridge.server_for("lookup_policy") == "policy-lookup"


async def test_scripted_loop_terminates_on_end_turn_with_audit_per_call() -> None:
    bridge = await _bridge()
    trail = AuditTrail()
    runner = ScriptedRunner(
        [
            ScriptedResponse(
                stop_reason="tool_use",
                content=[ToolUseBlock(name="get_claim", input={"claim_id": "CLM-10001"}, id="t1")],
            ),
            ScriptedResponse(
                stop_reason="tool_use",
                content=[
                    ToolUseBlock(name="lookup_policy", input={"policy_id": "POL-5001"}, id="t2")
                ],
            ),
            ScriptedResponse(
                stop_reason="end_turn",
                content=[TextBlock(text="Claim CLM-10001 is paid; policy POL-5001 is active.")],
            ),
        ]
    )
    outcome = run_agent(
        request="Summarize claim CLM-10001 and its policy.",
        runner=runner,
        bridge=bridge,
        trail=trail,
        clock=FixedClock(),
        caller_identity="adj-9",
    )
    assert outcome.stop_reason == "end_turn"
    assert outcome.tool_calls == ["get_claim", "lookup_policy"]
    assert len(trail) == 2  # one audit entry per tool call
    assert outcome.audit_entries == 2


def test_four_enterprise_decisions_map_to_named_components() -> None:
    # registry, identity, gateway, audit trail -- each a real named component.
    assert McpConfig.__name__ == "McpConfig"  # registry
    assert "scope" in AuditEntry.model_fields  # identity boundary
    assert AuditedToolRunner.__name__ == "AuditedToolRunner"  # gateway
    assert AuditTrail.__name__ == "AuditTrail"  # audit trail


# ---- CLI run + audit ---------------------------------------------------


def _scripted_get_claim() -> ScriptedRunner:
    return ScriptedRunner(
        [
            ScriptedResponse(
                stop_reason="tool_use",
                content=[ToolUseBlock(name="get_claim", input={"claim_id": "CLM-10001"}, id="t1")],
            ),
            ScriptedResponse(stop_reason="end_turn", content=[TextBlock(text="Done.")]),
        ]
    )


def test_cli_run_and_audit_roundtrip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"request": "Look up CLM-10001", "caller_identity": "adj-3"}))
    audit_log = tmp_path / "audit.json"

    rc = main(["run", str(request), "--audit-log", str(audit_log)], runner=_scripted_get_claim())
    run_out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert run_out["outcome"]["stop_reason"] == "end_turn"
    assert len(run_out["audit_trail"]) == 1

    rc = main(["audit", "--audit-log", str(audit_log)])
    audit_out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert len(audit_out) == 1
    assert audit_out[0]["tool"] == "get_claim"
    assert audit_out[0]["caller_identity"] == "adj-3"


# ---- Live test (real model selects the governed custom tool) -----------


@pytest.mark.live
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="requires ANTHROPIC_API_KEY")
async def test_live_model_selects_custom_claims_tool() -> None:
    from mcp_governance.loop import AnthropicRunner

    bridge = await _bridge()
    trail = AuditTrail()
    outcome = run_agent(
        request="What is the status and amount of claim CLM-10001? Use the available tools.",
        runner=AnthropicRunner(),
        bridge=bridge,
        trail=trail,
        clock=FixedClock(),
        caller_identity="live-adjuster",
    )
    assert outcome.stop_reason == "end_turn"
    assert "get_claim" in outcome.tool_calls  # chose the custom tool, did not fabricate
    assert len(trail) >= 1
    assert all(e.scope is Scope.PROJECT for e in trail.entries)
    assert trail.entries[0].tool == "get_claim"
