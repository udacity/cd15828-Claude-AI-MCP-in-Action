"""The bridge between the governed FastMCP servers and the Anthropic tool-use loop.

In a live Claude Code session the MCP client connects to each server over stdio, discovers
their tools, and presents them to the model. Here we do the same thing **in-process**: we
read each server's registered tools (descriptions + JSON schemas come straight from the
FastMCP registration, so they stay the single source of truth) and expose them as Anthropic
``tools`` definitions, dispatching calls back to the shared service logic. The bridge is the
in-process equivalent of what Claude Code's MCP client does over stdio.

Crucially the bridge combines tools from *all* configured servers so they are available to
the model **simultaneously** in one loop (exam K3).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from mcp_governance.scoping import Scope
from mcp_governance.servers import (
    build_claims_server,
    call_get_claim,
    call_lookup_policy,
    call_search_claims,
)
from mcp_governance.services import ClaimsService, PolicyService


class GovernedTool(BaseModel):
    """A tool exposed through the bridge, tagged with its origin server and scope."""

    name: str
    server: str
    scope: Scope
    description: str
    input_schema: dict[str, Any]


class Bridge:
    """Holds the combined tool catalog and dispatches calls to the service logic."""

    def __init__(
        self,
        tools: list[GovernedTool],
        claims_svc: ClaimsService,
        policy_svc: PolicyService,
    ) -> None:
        self._tools = {t.name: t for t in tools}
        self._claims = claims_svc
        self._policy = policy_svc

    # --- introspection ------------------------------------------------------------

    def tool_names(self) -> set[str]:
        return set(self._tools)

    def anthropic_tools(self) -> list[dict[str, Any]]:
        """All governed tools, from every server, as Anthropic tool definitions."""
        return [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in self._tools.values()
        ]

    def server_for(self, name: str) -> str:
        return self._tools[name].server

    def scope_for(self, name: str) -> Scope:
        return self._tools[name].scope

    # --- dispatch -----------------------------------------------------------------

    def dispatch(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "get_claim":
            return call_get_claim(self._claims, str(args["claim_id"]))
        if name == "search_claims":
            return call_search_claims(
                self._claims, args.get("status"), args.get("min_amount")
            )
        if name == "lookup_policy":
            return call_lookup_policy(self._policy, str(args["policy_id"]))
        raise KeyError(f"unknown tool {name!r}")


_SCOPE_BY_SERVER = {"claims-database": Scope.PROJECT, "policy-lookup": Scope.PROJECT}


async def build_bridge(
    claims_svc: ClaimsService | None = None,
    policy_svc: PolicyService | None = None,
) -> Bridge:
    """Construct the bridge by reading both servers' registered tools.

    The claims server is the source of both the claims tools and the schema resource; the
    policy server supplies ``lookup_policy``. Building the policy server inline keeps the
    bridge self-contained while still reading real FastMCP tool schemas."""
    from mcp_governance.servers import build_policy_server

    claims = claims_svc or ClaimsService.from_dir()
    policy = policy_svc or PolicyService.from_dir()

    tools: list[GovernedTool] = []
    # TODO (LO-6 / exam K3): read the registered tools from BOTH servers and expose them
    #   SIMULTANEOUSLY. The common under-build is to wire one server; the model must see
    #   every configured server's tools at once. For each (server, server_name) in
    #   build_claims_server(claims)/"claims-database" and build_policy_server(policy)/
    #   "policy-lookup": `for tool in await server.list_tools():` (list_tools is async)
    #   append a GovernedTool(name, server=server_name, scope=_SCOPE_BY_SERVER[server_name],
    #   description=tool.description or "", input_schema=tool.inputSchema).
    raise NotImplementedError

    return Bridge(tools, claims, policy)
