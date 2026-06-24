# Starter — Exercise 2: Custom Servers, Tool Descriptions & a Schema Resource

Implement the `# TODO` blocks, then verify. (Your Exercise 1 work is already in place.)

## Your TODOs

- [ ] `mcp_governance/decision.py` — `decide` (four rules, priority order) and `lint_description`
- [ ] `mcp_governance/contracts.py` — `CONTRACTS` (one `ToolContract` per tool)
- [ ] `mcp_governance/servers.py` — `_not_found` (structured error, never raise) and the
      `claims://schema` resource registration
- [ ] `mcp_governance/schema.py` — `build_schema_catalog`

## Verify

```bash
.venv/bin/pytest tests/test_servers.py tests/test_resource.py tests/test_decision.py
.venv/bin/mcp-governance decide
```
