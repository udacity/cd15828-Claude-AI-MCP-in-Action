# Exercise 1 — Scoped MCP Config Registry + Secret-Leak CI Gate

You start from the **bootstrap scaffold**: the full `mcp_governance` package skeleton, the
data corpus, the committed config fixtures, the Pydantic models, the `${VAR}` and
secret-prefix regexes, and the CLI — everything except the loader logic you write here.

## What you'll build

The **registry** and **identity** decisions, plus the merge-time **gateway**: a loader for
the project `.mcp.json` and the personal `~/.claude.json` that tags each by scope, expands
`${VAR}` credentials from a passed-in environment, and a CI gate that fails the build on a
committed secret or a missing referenced variable.

## Where you write code (all in `mcp_governance/scoping.py`)

- `load_project_config` / `load_personal_config` — tag the loaded config with the right
  scope. Scope is a **file-level** property: a whole `.mcp.json` is project scope, a whole
  `~/.claude.json` is personal — not per-server.
- `expand_env` — resolve every `${VAR}` token in each server's `args`/`env` from the
  passed-in environment. Expansion happens here, **once**; no module reads `os.environ`.
- `_looks_like_secret` — the leak rule. A `${VAR}` reference is externalized and is **never**
  a leak; only literal-looking credentials are.

## Run / verify

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_scoping.py                                  # all green when done
POLICY_API_KEY=x GITHUB_TOKEN=y .venv/bin/mcp-governance ci-check fixtures/.mcp.json   # exit 0
```

The clean fixtures should pass the gate (exit 0); a config with a literal token or a missing
referenced var should fail it (exit 1).
