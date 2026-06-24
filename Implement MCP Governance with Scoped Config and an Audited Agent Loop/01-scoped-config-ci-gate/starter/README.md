# Starter — Exercise 1: Scoped MCP Config Registry + Secret-Leak CI Gate

This is the bootstrap scaffold. Implement the `# TODO` blocks, then verify.

## Your TODOs (all in `mcp_governance/scoping.py`)

- [ ] `load_project_config` — tag the config with **project** scope
- [ ] `load_personal_config` — tag the config with **personal** scope
- [ ] `expand_env` — resolve `${VAR}` tokens from the passed-in environment, once
- [ ] `_looks_like_secret` — the leak rule (a `${VAR}` reference is safe; literals leak)

## Setup & verify

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_scoping.py
POLICY_API_KEY=x GITHUB_TOKEN=y .venv/bin/mcp-governance ci-check fixtures/.mcp.json   # exit 0 when done
```
