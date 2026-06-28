"""The MCP **registry** (enterprise decision #1) and the CI **gateway** at merge time.

This module loads Claude Code MCP config files, classifies their *scope* (project vs
personal -- the identity boundary), expands ``${VAR}`` credential references from the
environment at load time, and scans for plaintext credentials that should never be
committed. :func:`run_ci_check` composes those into a single pass/fail gate suitable for
a CI pipeline step (``mcp-governance ci-check .mcp.json``).

Design rule: credentials are *externalized* -- a config value either contains a
``${VAR}`` reference (safe, resolved from the environment) or it is a literal. A literal
that looks like a credential is a leak. Expansion happens here, once; no other module
reads ``os.environ`` for credentials.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

# A ${VAR} or ${VAR:-default} token.
_TOKEN = re.compile(r"\$\{(?P<var>[A-Za-z_][A-Za-z0-9_]*)(?::-(?P<default>[^}]*))?\}")

# Credential prefixes that are unambiguous on sight.
_SECRET_PREFIXES = ("sk-", "ghp_", "gho_", "ghs_", "github_pat_", "AKIA", "xoxb-", "xoxp-", "AIza")
# Env keys whose *name* implies the value is a credential.
_SECRET_KEY = re.compile(r"(token|key|secret|password|passwd|credential)", re.IGNORECASE)
# A high-entropy literal: 32+ chars drawn from a base64/hex-ish alphabet.
_HIGH_ENTROPY = re.compile(r"^[A-Za-z0-9+/=_\-]{32,}$")


class Scope(StrEnum):
    """The identity boundary a server is configured under."""

    PROJECT = "project"
    PERSONAL = "personal"


class ConfigError(ValueError):
    """A config file is missing, malformed, or structurally invalid."""


class MissingEnvVarError(ConfigError):
    """A ``${VAR}`` reference has no value in the environment and no default."""

    def __init__(self, var: str, server: str) -> None:
        self.var = var
        self.server = server
        super().__init__(
            f"server {server!r} references ${{{var}}} but it is not set and has no default"
        )


class McpServerConfig(BaseModel):
    """One entry under ``mcpServers`` in a Claude Code config file."""

    model_config = ConfigDict(extra="forbid")

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    type: str = "stdio"


class ScopedServer(BaseModel):
    """A server paired with the scope of the file it was declared in."""

    name: str
    config: McpServerConfig
    scope: Scope


class McpConfig(BaseModel):
    """A parsed MCP config file. A whole ``.mcp.json`` is project scope; a whole
    ``~/.claude.json`` is personal scope (Claude Code's actual semantics)."""

    mcpServers: dict[str, McpServerConfig]
    scope: Scope

    @property
    def servers(self) -> list[ScopedServer]:
        """Every server tagged with this file's scope."""
        return [
            ScopedServer(name=name, config=cfg, scope=self.scope)
            for name, cfg in self.mcpServers.items()
        ]


class SecretLeak(BaseModel):
    """A literal credential found where a ``${VAR}`` reference belongs."""

    server: str
    key: str
    reason: str


class MissingRef(BaseModel):
    """A ``${VAR}`` reference with no value available."""

    server: str
    key: str
    var: str


class CiViolation(BaseModel):
    """One reason the CI gate failed."""

    kind: str  # "config_error" | "secret_leak" | "missing_env_var"
    server: str | None
    detail: str


class CiReport(BaseModel):
    """The result of :func:`run_ci_check` -- maps directly to a CLI exit code."""

    path: str
    ok: bool
    servers: list[str] = Field(default_factory=list)
    violations: list[CiViolation] = Field(default_factory=list)


# --------------------------------------------------------------------------- load


def _load(path: str | Path, scope: Scope) -> McpConfig:
    p = Path(path)
    try:
        text = p.read_text()
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {p}") from exc
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"malformed JSON in {p}: {exc}") from exc
    if not isinstance(raw, dict) or "mcpServers" not in raw:
        raise ConfigError(f"{p}: missing required 'mcpServers' key")
    try:
        return McpConfig(mcpServers=raw["mcpServers"], scope=scope)
    except ValidationError as exc:
        raise ConfigError(f"{p}: invalid mcpServers structure: {exc}") from exc


def load_project_config(path: str | Path) -> McpConfig:
    """Load a project-scoped ``.mcp.json`` (shared, version-controlled)."""
    # TODO (LO-2): load this file and tag every server with PROJECT scope.
    #   Scope is a *file-level* property, not per-server: a whole .mcp.json is project
    #   scope. Delegate to _load(path, ...) with the right Scope.
    raise NotImplementedError


def load_personal_config(path: str | Path) -> McpConfig:
    """Load a personal-scoped ``~/.claude.json`` (individual workflows)."""
    # TODO (LO-2): load this file and tag every server with PERSONAL scope.
    #   A whole ~/.claude.json is personal scope. Delegate to _load(path, ...).
    raise NotImplementedError


# ----------------------------------------------------------------------- expansion


def _expand_value(value: str, environ: Mapping[str, str], server: str) -> str:
    def replace(match: re.Match[str]) -> str:
        var = match.group("var")
        if var in environ:
            return environ[var]
        default = match.group("default")
        if default is not None:
            return default
        raise MissingEnvVarError(var, server)

    return _TOKEN.sub(replace, value)


def expand_env(config: McpConfig, environ: Mapping[str, str]) -> McpConfig:
    """Return a copy of ``config`` with every ``${VAR}`` token in ``env`` values and
    ``args`` resolved from ``environ``. Raises :class:`MissingEnvVarError` for the first
    reference that is absent and has no ``:-default``."""
    # TODO (LO-1): build a new McpConfig whose every server has its `args` and `env`
    #   values run through _expand_value(...). Expansion happens HERE, once, from the
    #   passed-in `environ` -- no module reads os.environ for credentials. Values with no
    #   ${...} token pass through unchanged; a missing referenced var raises
    #   MissingEnvVarError (handled by _expand_value).
    raise NotImplementedError


def find_missing_env_vars(config: McpConfig, environ: Mapping[str, str]) -> list[MissingRef]:
    """Collect *all* ``${VAR}`` references that cannot be resolved (no value, no default)
    -- the CI gate reports every offender, not just the first."""
    missing: list[MissingRef] = []
    for name, cfg in config.mcpServers.items():
        items = list(cfg.env.items()) + [(f"args[{i}]", a) for i, a in enumerate(cfg.args)]
        for key, value in items:
            for match in _TOKEN.finditer(value):
                var = match.group("var")
                if var not in environ and match.group("default") is None:
                    missing.append(MissingRef(server=name, key=key, var=var))
    return missing


# -------------------------------------------------------------------- secret scan


def _looks_like_secret(key: str, value: str) -> str | None:
    """Return a human-readable reason if ``value`` looks like a committed credential,
    else ``None``. A value containing a ``${...}`` reference is considered externalized
    and is never a leak."""
    # TODO (LO-1): implement the leak rule. A ${VAR} reference is EXTERNALIZED and is
    #   NEVER a leak (this is the common false positive -- guard for "${" first).
    #   Flag a leak (return a reason string) when the literal value: begins with a known
    #   credential prefix (_SECRET_PREFIXES); OR sits under a credential-named key
    #   (_SECRET_KEY) as a non-empty literal; OR is a high-entropy blob (_HIGH_ENTROPY).
    #   Otherwise return None.
    raise NotImplementedError


def scan_for_secrets(config: McpConfig) -> list[SecretLeak]:
    """Scan an (unexpanded) config for plaintext credentials. A config whose credentials
    are all ``${VAR}`` references yields an empty list."""
    leaks: list[SecretLeak] = []
    for name, cfg in config.mcpServers.items():
        for key, value in cfg.env.items():
            reason = _looks_like_secret(key, value)
            if reason:
                leaks.append(SecretLeak(server=name, key=key, reason=reason))
        for i, arg in enumerate(cfg.args):
            reason = _looks_like_secret(f"args[{i}]", arg)
            if reason:
                leaks.append(SecretLeak(server=name, key=f"args[{i}]", reason=reason))
    return leaks


# ------------------------------------------------------------------------ CI gate


def run_ci_check(
    path: str | Path, environ: Mapping[str, str], scope: Scope = Scope.PROJECT
) -> CiReport:
    """Run the full governance gate against a config file: parse -> referenced-env-present
    -> secret scan. The returned report's ``ok`` flag is the CI pass/fail."""
    path_str = str(path)
    try:
        config = _load(path, scope)
    except ConfigError as exc:
        return CiReport(
            path=path_str,
            ok=False,
            violations=[CiViolation(kind="config_error", server=None, detail=str(exc))],
        )

    violations: list[CiViolation] = []
    for leak in scan_for_secrets(config):
        violations.append(
            CiViolation(kind="secret_leak", server=leak.server, detail=f"{leak.key}: {leak.reason}")
        )
    for ref in find_missing_env_vars(config, environ):
        violations.append(
            CiViolation(
                kind="missing_env_var",
                server=ref.server,
                detail=f"{ref.key} references ${{{ref.var}}} which is not set",
            )
        )

    return CiReport(
        path=path_str,
        ok=not violations,
        servers=sorted(config.mcpServers),
        violations=violations,
    )
