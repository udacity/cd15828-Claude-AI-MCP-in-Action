# Solution — Exercise 1: Scoped MCP Config Registry + Secret-Leak CI Gate

The completed `mcp_governance/scoping.py` (`load_project_config` / `load_personal_config`
scope tagging, `expand_env`, `_looks_like_secret`). Modules for later exercises are still
stubbed, so verify with the scoped command.

```bash
.venv/bin/pytest tests/test_scoping.py          # 19 passed
POLICY_API_KEY=x GITHUB_TOKEN=y .venv/bin/mcp-governance ci-check fixtures/.mcp.json   # exit 0
```
