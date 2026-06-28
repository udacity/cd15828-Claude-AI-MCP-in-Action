# Solution — Exercise 3: Audited Agent Loop + Append-Only Audit Trail

The completed project — this equals the reference solution. All modules are implemented:
`audit.py`, `bridge.py`, and `loop.py` complete the gateway and audit trail.

```bash
.venv/bin/pytest                      # 63 passed, 1 skipped (the live test)
.venv/bin/pytest -m live              # optional, needs ANTHROPIC_API_KEY
.venv/bin/mcp-governance run request.json --audit-log /tmp/audit.json
.venv/bin/mcp-governance audit --audit-log /tmp/audit.json
```

**Scope of this tree:** `mcp_governance/`, `tests/`, `data/`, and `fixtures/` make up the
complete project. Only build artifacts (caches, `.venv/`) are omitted.
