"""The two **custom** MCP servers the registry declares: ``claims-database`` and
``policy-lookup``.

These are real FastMCP servers. Each tool is a thin wrapper over the service layer, and
its description comes from :data:`~mcp_governance.contracts.CONTRACTS` so descriptions stay
the single source of truth. ``claims-database`` also exposes the ``claims://schema``
resource. The tool *functions* (``call_get_claim`` etc.) are module-level so the
bridge can dispatch to the exact same logic the server registers.

The project ``.mcp.json`` points at this module: ``python -m mcp_governance.servers claims``
runs the claims server over stdio; ``... policy`` runs the policy server.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_governance.contracts import CONTRACTS
from mcp_governance.models import Claim
from mcp_governance.schema import build_schema_catalog
from mcp_governance.services import ClaimsService, PolicyService

CLAIMS_TOOLS = frozenset({"get_claim", "search_claims"})
POLICY_TOOLS = frozenset({"lookup_policy"})
SCHEMA_RESOURCE_URI = "claims://schema"


def _not_found(kind: str, identifier: str) -> dict[str, Any]:
    """Graceful Tool Failure: a structured error result, never a raised exception."""
    return {
        "found": False,
        "is_error": True,
        "error_category": "not_found",
        "reason": f"no {kind} found with id {identifier!r}",
    }


def _claim_wire(claim: Claim) -> dict[str, Any]:
    return {"found": True, "is_error": False, **claim.model_dump()}


# --- tool implementations (shared by the FastMCP servers and the bridge) ------


def call_get_claim(svc: ClaimsService, claim_id: str) -> dict[str, Any]:
    claim = svc.get_claim(claim_id)
    return _claim_wire(claim) if claim is not None else _not_found("claim", claim_id)


def call_search_claims(
    svc: ClaimsService, status: str | None = None, min_amount: float | None = None
) -> dict[str, Any]:
    matches = svc.search_claims(status=status, min_amount=min_amount)
    return {
        "found": True,
        "is_error": False,
        "count": len(matches),
        "claims": [c.model_dump() for c in matches],
    }


def call_lookup_policy(svc: PolicyService, policy_id: str) -> dict[str, Any]:
    policy = svc.lookup_policy(policy_id)
    if policy is None:
        return _not_found("policy", policy_id)
    return {"found": True, "is_error": False, **policy.model_dump()}


# --- server construction -----------------------------------------------------------


def build_claims_server(service: ClaimsService | None = None) -> FastMCP:
    """The ``claims-database`` server: two tools + the ``claims://schema`` resource."""
    svc = service or ClaimsService.from_dir()
    server = FastMCP("claims-database")

    @server.tool(name="get_claim", description=CONTRACTS["get_claim"].render())
    def get_claim(claim_id: str) -> dict[str, Any]:
        return call_get_claim(svc, claim_id)

    @server.tool(name="search_claims", description=CONTRACTS["search_claims"].render())
    def search_claims(status: str | None = None, min_amount: float | None = None) -> dict[str, Any]:
        return call_search_claims(svc, status, min_amount)

    @server.resource(
        SCHEMA_RESOURCE_URI,
        name="claims-schema",
        description="Field catalog for claim records (discover fields without exploratory calls).",
        mime_type="application/json",
    )
    def schema_resource() -> str:
        return json.dumps(build_schema_catalog(), indent=2)

    return server


def build_policy_server(service: PolicyService | None = None) -> FastMCP:
    """The ``policy-lookup`` server: one tool over the policy system of record."""
    svc = service or PolicyService.from_dir()
    server = FastMCP("policy-lookup")

    @server.tool(name="lookup_policy", description=CONTRACTS["lookup_policy"].render())
    def lookup_policy(policy_id: str) -> dict[str, Any]:
        return call_lookup_policy(svc, policy_id)

    return server


def main(argv: list[str] | None = None) -> int:
    """stdio entry point referenced by ``.mcp.json``."""
    args = sys.argv[1:] if argv is None else argv
    which = args[0] if args else "claims"
    server = build_claims_server() if which == "claims" else build_policy_server()
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
