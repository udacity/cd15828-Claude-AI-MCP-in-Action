"""Custom claims/policy FastMCP servers + built-in-resistant tool descriptions."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_governance.contracts import CONTRACTS
from mcp_governance.models import Claim, ClaimStatus, IncidentType, Policy
from mcp_governance.servers import (
    CLAIMS_TOOLS,
    POLICY_TOOLS,
    build_claims_server,
    build_policy_server,
    call_get_claim,
    call_lookup_policy,
)
from mcp_governance.services import ClaimsService, PolicyService

CLAIMS = [
    Claim(
        claim_id="CLM-1",
        policy_id="POL-1",
        claimant_name="A. Person",
        status=ClaimStatus.UNDER_REVIEW,
        incident_type=IncidentType.AUTO_COLLISION,
        amount=12000.0,
        filed_date="2024-05-01",
        adjuster="Karen Liu",
    ),
    Claim(
        claim_id="CLM-2",
        policy_id="POL-2",
        claimant_name="B. Person",
        status=ClaimStatus.PAID,
        incident_type=IncidentType.THEFT,
        amount=900.0,
        filed_date="2024-06-01",
        adjuster="Tom Reyes",
    ),
]
POLICIES = [
    Policy(
        policy_id="POL-1",
        holder_name="A. Person",
        policy_type="auto",
        coverage_limit=100000,
        deductible=1000,
        status="active",
        effective_date="2022-01-01",
    )
]


# ---- Service layer, independent of FastMCP ----------------------------


def test_get_claim_hit_and_miss() -> None:
    svc = ClaimsService(CLAIMS)
    assert svc.get_claim("CLM-1") is not None
    assert svc.get_claim("CLM-1").claim_id == "CLM-1"
    assert svc.get_claim("CLM-404") is None


def test_search_claims_filters_by_status_and_amount() -> None:
    svc = ClaimsService(CLAIMS)
    assert {c.claim_id for c in svc.search_claims()} == {"CLM-1", "CLM-2"}
    assert {c.claim_id for c in svc.search_claims(status="under_review")} == {"CLM-1"}
    assert {c.claim_id for c in svc.search_claims(min_amount=1000)} == {"CLM-1"}
    assert {c.claim_id for c in svc.search_claims(status=ClaimStatus.PAID)} == {"CLM-2"}


def test_lookup_policy_hit_and_miss() -> None:
    svc = PolicyService(POLICIES)
    assert svc.lookup_policy("POL-1") is not None
    assert svc.lookup_policy("POL-404") is None


def test_services_load_from_committed_data() -> None:
    claims = ClaimsService.from_dir()
    policies = PolicyService.from_dir()
    assert claims.get_claim("CLM-10001") is not None
    assert policies.lookup_policy("POL-5001") is not None


# ---- Graceful tool failure (structured error, never raises) -----------


def test_tool_not_found_returns_structured_error() -> None:
    svc = ClaimsService(CLAIMS)
    result = call_get_claim(svc, "CLM-404")
    assert result["found"] is False
    assert result["is_error"] is True
    assert result["error_category"] == "not_found"
    assert "CLM-404" in result["reason"]


def test_tool_hit_returns_record() -> None:
    result = call_get_claim(ClaimsService(CLAIMS), "CLM-1")
    assert result["found"] is True and result["is_error"] is False
    assert result["claim_id"] == "CLM-1"


def test_policy_not_found_structured_error() -> None:
    result = call_lookup_policy(PolicyService(POLICIES), "POL-404")
    assert result["found"] is False and result["error_category"] == "not_found"


# ---- Registered tool sets + descriptions from CONTRACTS -----


async def _tool_map(server: FastMCP) -> dict[str, str]:
    return {t.name: (t.description or "") for t in await server.list_tools()}


async def test_claims_server_exposes_exact_tool_set() -> None:
    tools = await _tool_map(build_claims_server(ClaimsService(CLAIMS)))
    assert set(tools) == set(CLAIMS_TOOLS) == {"get_claim", "search_claims"}


async def test_policy_server_exposes_exact_tool_set() -> None:
    tools = await _tool_map(build_policy_server(PolicyService(POLICIES)))
    assert set(tools) == set(POLICY_TOOLS) == {"lookup_policy"}


async def test_tool_descriptions_equal_contract_render() -> None:
    tools = await _tool_map(build_claims_server(ClaimsService(CLAIMS)))
    for name, description in tools.items():
        assert description == CONTRACTS[name].render()
        assert description.strip()  # non-empty


def test_contract_render_has_three_fallback_resistant_elements() -> None:
    for contract in CONTRACTS.values():
        rendered = contract.render().lower()
        assert "use this when" in rendered  # (1) when-to-use trigger
        assert "instead of" in rendered  # (2) built-in differentiation
        assert "example:" in rendered  # (3) concrete example
