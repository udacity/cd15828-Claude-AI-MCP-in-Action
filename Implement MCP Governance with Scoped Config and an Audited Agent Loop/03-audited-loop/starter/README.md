# Starter — Exercise 3: Audited Agent Loop + Append-Only Audit Trail

Implement the `# TODO` blocks, then verify. (Your Exercise 1–2 work is already in place.)
Finishing this exercise brings the project to the full reference solution.

## Your TODOs

- [ ] `mcp_governance/audit.py` — `arg_digest`, `AuditTrail.record` (append-only),
      `AuditedToolRunner.run` (the gateway: one entry per call)
- [ ] `mcp_governance/bridge.py` — `build_bridge` tool-collection loop (read **both** servers)
- [ ] `mcp_governance/loop.py` — `run_agent` (the `stop_reason` loop)

## Verify

```bash
.venv/bin/pytest                      # whole suite green
.venv/bin/pytest -m live              # optional, needs ANTHROPIC_API_KEY
```
