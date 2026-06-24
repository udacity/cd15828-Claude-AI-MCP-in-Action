# Exercise 3 — Audited Agent Loop + Append-Only Audit Trail

Picking up from Exercise 2: the governed servers, descriptions, and schema resource exist.
Now you run them under audit — completing the **gateway** and **audit trail** decisions, so
every governed tool call is recorded and a real model can be steered to the custom tool.

## What you'll build

- `arg_digest` — a stable hash so a raw `claim_id` never lands in the trail in cleartext.
- The **append-only** `AuditTrail.record` and the `AuditedToolRunner` **gateway** every
  governed call passes through (one audit entry per call, on success and error).
- The **bridge merge** that exposes *both* servers' tools to the model simultaneously
  (exam K3) — the common under-build is to wire only one.
- The `stop_reason`-driven `run_agent` loop.

When this exercise is complete, the project equals the full reference solution.

## Where you write code

- `mcp_governance/audit.py` — `arg_digest`, `AuditTrail.record`, `AuditedToolRunner.run`.
- `mcp_governance/bridge.py` — the `build_bridge` tool-collection loop (read both servers).
- `mcp_governance/loop.py` — `run_agent` (the `stop_reason` loop through the gateway).

## Run / verify

```bash
.venv/bin/pytest                                  # the whole suite is green (= reference)
# Optional, needs ANTHROPIC_API_KEY — proves a real model picks the governed custom tool:
.venv/bin/mcp-governance run request.json --audit-log /tmp/audit.json
.venv/bin/mcp-governance audit --audit-log /tmp/audit.json
.venv/bin/pytest -m live
```
