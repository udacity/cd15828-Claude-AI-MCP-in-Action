"""Build-vs-reuse decision engine and the tool-description quality linter.

The decision framework (exam Task 2.4 S4) makes the community-vs-custom call defensible:
proprietary or PII-bearing data must live in a server the team controls (custom); a mature
community server covering a generic, low-customization need should be reused.

The linter operationalizes "enhance tool descriptions to prevent built-in-tool preference"
(exam S3 / Playbook "MCP Tool Specificity") by scoring a description for the three
fallback-resistant elements the contracts carry.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from mcp_governance.config import INTEGRATION_NEEDS_PATH


class Level(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Choice(StrEnum):
    COMMUNITY = "community"
    CUSTOM = "custom"


class IntegrationNeed(BaseModel):
    """One integration the team must decide how to satisfy."""

    name: str
    proprietary_data: bool
    community_server_exists: bool
    handles_pii: bool
    customization: Level
    maintenance_capacity: Level
    expected: Choice | None = None  # documented expectation for the committed matrix


class Recommendation(BaseModel):
    need: str
    recommendation: Choice
    rationale: str
    deciding_factors: list[str] = Field(default_factory=list)


def decide(need: IntegrationNeed) -> Recommendation:
    """Apply the build-vs-reuse framework. Rules are evaluated in priority order; the first
    that fires sets the recommendation and names the deciding factor."""
    factors: list[str] = []

    if need.proprietary_data or need.handles_pii:
        if need.proprietary_data:
            factors.append("proprietary_data")
        if need.handles_pii:
            factors.append("handles_pii")
        return Recommendation(
            need=need.name,
            recommendation=Choice.CUSTOM,
            rationale=(
                "Build a custom server: the integration handles proprietary and/or PII data "
                "that must stay inside a server the team controls, with its own access "
                "controls and audit trail."
            ),
            deciding_factors=factors,
        )

    if not need.community_server_exists:
        return Recommendation(
            need=need.name,
            recommendation=Choice.CUSTOM,
            rationale=(
                "Build a custom server: no mature community server exists for this need, so "
                "there is nothing to reuse."
            ),
            deciding_factors=["no_community_server"],
        )

    if need.customization is Level.HIGH:
        return Recommendation(
            need=need.name,
            recommendation=Choice.CUSTOM,
            rationale=(
                "Build a custom server: although a community server exists, the required "
                "customization is high enough that adapting the community server costs more "
                "than owning a purpose-built one (a borderline call)."
            ),
            deciding_factors=["community_server_exists", "high_customization"],
        )

    return Recommendation(
        need=need.name,
        recommendation=Choice.COMMUNITY,
        rationale=(
            "Reuse the community server: a mature server already covers this generic, "
            "low/medium-customization need on non-proprietary data, so building custom would "
            "duplicate maintained work."
        ),
        deciding_factors=["community_server_exists", "non_proprietary"],
    )


def load_integration_needs(path: Path = INTEGRATION_NEEDS_PATH) -> list[IntegrationNeed]:
    return [IntegrationNeed.model_validate(r) for r in json.loads(path.read_text())]


def decision_matrix(needs: list[IntegrationNeed] | None = None) -> list[Recommendation]:
    return [decide(n) for n in (needs if needs is not None else load_integration_needs())]


# ------------------------------------------------------------------- description linter


class DescriptionScore(BaseModel):
    score: int
    max_score: int = 3
    missing: list[str] = Field(default_factory=list)

    @property
    def passes(self) -> bool:
        return self.score == self.max_score


def lint_description(text: str) -> DescriptionScore:
    """Score a tool description for the three built-in-fallback-resistant qualities."""
    lowered = text.lower()
    checks = {
        "when_to_use": "use this when" in lowered,
        "builtin_differentiation": "instead of" in lowered,
        "concrete_example": "example:" in lowered,
    }
    missing = [name for name, present in checks.items() if not present]
    return DescriptionScore(score=sum(checks.values()), missing=missing)
