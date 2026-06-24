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
    # TODO (LO-4): evaluate the rules in PRIORITY order; the first that fires wins and names
    #   its deciding_factors. Every Recommendation needs a non-empty rationale.
    #     1. proprietary_data OR handles_pii  -> CUSTOM (the team must own the system of
    #        record and its access controls; never hand PII to a community server).
    #     2. not community_server_exists      -> CUSTOM (nothing mature to reuse).
    #     3. customization is Level.HIGH      -> CUSTOM (adapting the community server costs
    #        more than owning a purpose-built one -- the borderline call).
    #     4. otherwise                        -> COMMUNITY (reuse a mature server for a
    #        generic, non-proprietary, low/medium-customization need).
    raise NotImplementedError


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
    # TODO (LO-5): score `text` 0-3 and list the missing elements. Check (case-insensitively)
    #   for the three qualities a built-in-resistant description carries:
    #     - when_to_use             -> contains "use this when"
    #     - builtin_differentiation -> contains "instead of"
    #     - concrete_example        -> contains "example:"
    #   Return DescriptionScore(score=<count present>, missing=[<names absent>]).
    #   This is the SAME bar your own CONTRACTS descriptions must clear (the project
    #   dogfoods its quality bar: every contract description must score the maximum).
    raise NotImplementedError
