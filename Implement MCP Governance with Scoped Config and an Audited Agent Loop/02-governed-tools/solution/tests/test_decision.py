"""Build-vs-reuse decision engine + tool-description quality linter."""

from __future__ import annotations

import pytest

from mcp_governance.cli import main
from mcp_governance.contracts import CONTRACTS
from mcp_governance.decision import (
    Choice,
    IntegrationNeed,
    Level,
    decide,
    decision_matrix,
    lint_description,
    load_integration_needs,
)


def _need(**overrides: object) -> IntegrationNeed:
    base: dict[str, object] = dict(
        name="x",
        proprietary_data=False,
        community_server_exists=True,
        handles_pii=False,
        customization=Level.LOW,
        maintenance_capacity=Level.HIGH,
    )
    base.update(overrides)
    return IntegrationNeed.model_validate(base)


# ---- Decision rules ---------------------------------------------------


def test_proprietary_data_forces_custom() -> None:
    rec = decide(_need(proprietary_data=True, community_server_exists=True))
    assert rec.recommendation is Choice.CUSTOM
    assert "proprietary_data" in rec.deciding_factors


def test_pii_forces_custom() -> None:
    rec = decide(_need(handles_pii=True))
    assert rec.recommendation is Choice.CUSTOM
    assert "handles_pii" in rec.deciding_factors


def test_mature_community_server_yields_community() -> None:
    rec = decide(_need(community_server_exists=True, customization=Level.LOW))
    assert rec.recommendation is Choice.COMMUNITY
    assert rec.rationale


def test_no_community_server_yields_custom() -> None:
    rec = decide(_need(community_server_exists=False))
    assert rec.recommendation is Choice.CUSTOM
    assert "no_community_server" in rec.deciding_factors


def test_high_customization_with_community_is_borderline_custom() -> None:
    rec = decide(_need(community_server_exists=True, customization=Level.HIGH))
    assert rec.recommendation is Choice.CUSTOM
    assert "high_customization" in rec.deciding_factors


# ---- The committed 5-scenario matrix ----------------------------------


def test_matrix_has_five_needs_with_expected_recommendations() -> None:
    needs = load_integration_needs()
    assert len(needs) == 5
    recs = decision_matrix(needs)
    for need, rec in zip(needs, recs, strict=True):
        assert need.expected is not None
        assert rec.recommendation is need.expected, f"{need.name}: {rec.recommendation}"
        assert rec.rationale.strip()
        assert rec.deciding_factors


def test_matrix_covers_both_custom_and_community() -> None:
    choices = {r.recommendation for r in decision_matrix()}
    assert choices == {Choice.CUSTOM, Choice.COMMUNITY}


def test_decide_cli_renders_table(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["decide"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "RECOMMENDATION" in captured
    assert "claims database" in captured


# ---- The description linter ---------------------------------


def test_bare_description_scores_below_threshold() -> None:
    score = lint_description("Gets a claim.")
    assert score.score < 3
    assert not score.passes
    assert set(score.missing) == {"when_to_use", "builtin_differentiation", "concrete_example"}


def test_partial_description_reports_missing_elements() -> None:
    score = lint_description("Use this when you have a claim ID. Example: get_claim('CLM-1')")
    assert "builtin_differentiation" in score.missing
    assert score.score == 2


def test_all_contract_descriptions_pass_at_full_score() -> None:
    for name, contract in CONTRACTS.items():
        score = lint_description(contract.render())
        assert score.passes, f"{name} missing {score.missing}"
        assert score.score == 3
        assert score.missing == []
