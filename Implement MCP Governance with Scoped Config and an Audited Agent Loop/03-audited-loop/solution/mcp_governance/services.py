"""Service layer over the local claim/policy records.

Deliberately independent of FastMCP and the Anthropic SDK so the business logic is
unit-testable on its own. The servers (``servers.py``) are thin wrappers.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_governance.config import CLAIMS_DIR, POLICIES_DIR
from mcp_governance.models import Claim, ClaimStatus, Policy


def _load_records(directory: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text())
        if isinstance(data, list):
            records.extend(data)
        else:
            records.append(data)
    return records


class ClaimsService:
    """In-memory query layer over claim records."""

    def __init__(self, claims: list[Claim]) -> None:
        self._claims = claims
        self._by_id = {c.claim_id: c for c in claims}

    @classmethod
    def from_dir(cls, directory: Path = CLAIMS_DIR) -> ClaimsService:
        return cls([Claim.model_validate(r) for r in _load_records(directory)])

    def get_claim(self, claim_id: str) -> Claim | None:
        return self._by_id.get(claim_id)

    def search_claims(
        self, status: ClaimStatus | str | None = None, min_amount: float | None = None
    ) -> list[Claim]:
        results = self._claims
        if status is not None:
            status_value = status.value if isinstance(status, ClaimStatus) else status
            results = [c for c in results if c.status.value == status_value]
        if min_amount is not None:
            results = [c for c in results if c.amount >= min_amount]
        return list(results)


class PolicyService:
    """In-memory query layer over policy records."""

    def __init__(self, policies: list[Policy]) -> None:
        self._by_id = {p.policy_id: p for p in policies}

    @classmethod
    def from_dir(cls, directory: Path = POLICIES_DIR) -> PolicyService:
        return cls([Policy.model_validate(r) for r in _load_records(directory)])

    def lookup_policy(self, policy_id: str) -> Policy | None:
        return self._by_id.get(policy_id)
