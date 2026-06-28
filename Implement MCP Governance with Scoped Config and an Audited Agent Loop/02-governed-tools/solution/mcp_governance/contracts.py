"""Tool contracts -- the single source of truth for every MCP tool description.

Each description is engineered to resist the failure mode from the Architect's Playbook's
"MCP Tool Specificity" (p23): an agent defaulting to a generic built-in (web search, file
grep) instead of the authoritative custom tool. Every contract therefore carries the three
fallback-resistant elements the linter checks for:

1. an explicit **"Use this when ..."** trigger,
2. explicit **differentiation** from the generic built-in ("Use this instead of ..."),
3. a concrete **Example:** invocation.

``render()`` is what gets registered as the tool's wire description in *both* the FastMCP
server and the Anthropic bridge -- never restated in the system prompt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContract:
    name: str
    summary: str
    when_to_use: str
    instead_of: str
    example: str

    def render(self) -> str:
        return (
            f"{self.summary}\n"
            f"Use this when {self.when_to_use}\n"
            f"{self.instead_of}\n"
            f"Example: {self.example}"
        )


CONTRACTS: dict[str, ToolContract] = {
    "get_claim": ToolContract(
        name="get_claim",
        summary=(
            "Fetch a single insurance claim record by its claim ID from the Northwind "
            "Mutual claims database, the authoritative system of record for claims."
        ),
        when_to_use=(
            "you have a claim ID (format CLM-#####) and need its current status, claimed "
            "amount, incident type, linked policy, or assigned adjuster."
        ),
        instead_of=(
            "Use this instead of a generic web search or file grep: claim data is "
            "proprietary, exists only in this database, and is never on the public web."
        ),
        example='get_claim(claim_id="CLM-10001")',
    ),
    "search_claims": ToolContract(
        name="search_claims",
        summary="Search the claims database, optionally filtering by status and minimum amount.",
        when_to_use=(
            "you need to list or filter claims (e.g. every under_review claim over $10,000) "
            "rather than fetch one already-known claim ID."
        ),
        instead_of=(
            "Use this instead of fetching claims one ID at a time or guessing which exist: "
            "it queries the authoritative claims database directly."
        ),
        example='search_claims(status="under_review", min_amount=10000)',
    ),
    "lookup_policy": ToolContract(
        name="lookup_policy",
        summary=(
            "Look up an insurance policy by its policy ID from the policy system of record."
        ),
        when_to_use=(
            "you have a policy ID (format POL-####) and need the coverage limit, deductible, "
            "policy type, holder, or policy status."
        ),
        instead_of=(
            "Use this instead of a web search or an assumption: policy terms are proprietary "
            "and authoritative only in this server."
        ),
        example='lookup_policy(policy_id="POL-5001")',
    ),
}
