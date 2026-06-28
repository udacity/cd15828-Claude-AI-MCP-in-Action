"""Scoped MCP config registry, env-var expansion, secret-leak CI gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_governance.cli import main
from mcp_governance.config import FIXTURES_DIR
from mcp_governance.scoping import (
    ConfigError,
    MissingEnvVarError,
    Scope,
    expand_env,
    find_missing_env_vars,
    load_personal_config,
    load_project_config,
    run_ci_check,
    scan_for_secrets,
)

PROJECT_FIXTURE = FIXTURES_DIR / ".mcp.json"
PERSONAL_FIXTURE = FIXTURES_DIR / "claude.json"
FULL_ENV = {
    "POLICY_API_KEY": "pk_live_secret",
    "GITHUB_TOKEN": "ghp_realtoken",
    "BRAVE_API_KEY": "bk",
}


# ---- Typed models + scope tagging + typed errors ----------------------


def test_models_parse_and_tag_project_scope() -> None:
    config = load_project_config(PROJECT_FIXTURE)
    assert config.scope is Scope.PROJECT
    assert set(config.mcpServers) == {"claims-database", "policy-lookup", "github"}
    # every server is tagged with the file's scope
    assert {s.scope for s in config.servers} == {Scope.PROJECT}
    claims = config.mcpServers["claims-database"]
    assert claims.command == "python"
    assert claims.type == "stdio"


def test_personal_config_tagged_personal_scope() -> None:
    config = load_personal_config(PERSONAL_FIXTURE)
    assert config.scope is Scope.PERSONAL
    assert "underwriter-research" in config.mcpServers
    assert {s.scope for s in config.servers} == {Scope.PERSONAL}


def test_malformed_json_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / ".mcp.json"
    bad.write_text("{ not valid json ")
    with pytest.raises(ConfigError):
        load_project_config(bad)


def test_missing_mcpservers_key_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / ".mcp.json"
    bad.write_text(json.dumps({"servers": {}}))
    with pytest.raises(ConfigError):
        load_project_config(bad)


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_project_config(tmp_path / "nope.json")


# ---- Env-var expansion ------------------------------------------------


def test_expand_env_resolves_all_tokens() -> None:
    config = load_project_config(PROJECT_FIXTURE)
    expanded = expand_env(config, FULL_ENV)
    blob = json.dumps(expanded.model_dump())
    assert "${" not in blob  # no tokens remain
    assert expanded.mcpServers["policy-lookup"].env["POLICY_API_KEY"] == "pk_live_secret"
    assert expanded.mcpServers["github"].env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "ghp_realtoken"


def test_expand_env_missing_var_raises_named_error() -> None:
    config = load_project_config(PROJECT_FIXTURE)
    with pytest.raises(MissingEnvVarError) as exc:
        expand_env(config, {"GITHUB_TOKEN": "x"})  # POLICY_API_KEY absent
    assert exc.value.var == "POLICY_API_KEY"
    assert exc.value.server == "policy-lookup"


def test_expand_env_default_value_used(tmp_path: Path) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps(
            {"mcpServers": {"s": {"command": "x", "env": {"LEVEL": "${LOG_LEVEL:-info}"}}}}
        )
    )
    expanded = expand_env(load_project_config(cfg), {})
    assert expanded.mcpServers["s"].env["LEVEL"] == "info"


def test_literal_values_pass_through_unchanged() -> None:
    config = load_project_config(PROJECT_FIXTURE)
    expanded = expand_env(config, FULL_ENV)
    assert expanded.mcpServers["claims-database"].args == ["-m", "mcp_governance.servers", "claims"]


def test_find_missing_env_vars_collects_all() -> None:
    config = load_project_config(PROJECT_FIXTURE)
    missing = find_missing_env_vars(config, {})  # nothing set
    vars_missing = {m.var for m in missing}
    assert vars_missing == {"POLICY_API_KEY", "GITHUB_TOKEN"}


# ---- Secret scan; committed fixtures are clean -------------


def test_clean_fixtures_have_zero_leaks() -> None:
    assert scan_for_secrets(load_project_config(PROJECT_FIXTURE)) == []
    assert scan_for_secrets(load_personal_config(PERSONAL_FIXTURE)) == []


def test_planted_literal_token_is_flagged(tmp_path: Path) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "github": {
                        "command": "npx",
                        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_AAAAAAAAAAAAAAAAAAAA"},
                    }
                }
            }
        )
    )
    leaks = scan_for_secrets(load_project_config(cfg))
    assert len(leaks) == 1
    assert leaks[0].server == "github"
    assert "ghp_" in leaks[0].reason


def test_credential_named_key_with_literal_is_flagged(tmp_path: Path) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"s": {"command": "x", "env": {"API_KEY": "hunter2"}}}})
    )
    leaks = scan_for_secrets(load_project_config(cfg))
    assert len(leaks) == 1 and leaks[0].key == "API_KEY"


def test_reference_value_is_not_a_leak(tmp_path: Path) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"s": {"command": "x", "env": {"API_KEY": "${API_KEY}"}}}})
    )
    assert scan_for_secrets(load_project_config(cfg)) == []


def test_non_credential_literal_is_not_a_leak(tmp_path: Path) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps({"mcpServers": {"s": {"command": "x", "env": {"LOG_LEVEL": "debug"}}}})
    )
    assert scan_for_secrets(load_project_config(cfg)) == []


# ---- ci-check CLI exit codes ------------------------------------------


def test_ci_check_clean_fixture_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["ci-check", str(PROJECT_FIXTURE)], environ=FULL_ENV)
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["servers"] == ["claims-database", "github", "policy-lookup"]
    assert out["violations"] == []


def test_ci_check_planted_secret_exit_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(
        json.dumps(
            {"mcpServers": {"s": {"command": "x", "env": {"TOKEN": "ghp_DEADBEEFDEADBEEFDEAD"}}}}
        )
    )
    rc = main(["ci-check", str(cfg)], environ=FULL_ENV)
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert out["ok"] is False
    assert any(v["kind"] == "secret_leak" and v["server"] == "s" for v in out["violations"])


def test_ci_check_missing_env_var_exit_one(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["ci-check", str(PROJECT_FIXTURE)], environ={"GITHUB_TOKEN": "x"})
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert any(
        v["kind"] == "missing_env_var" and "POLICY_API_KEY" in v["detail"]
        for v in out["violations"]
    )


def test_run_ci_check_report_shape() -> None:
    report = run_ci_check(PROJECT_FIXTURE, FULL_ENV)
    assert report.ok and report.path.endswith(".mcp.json")
