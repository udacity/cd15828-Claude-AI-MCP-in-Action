# Exercise 3 — Distributing Tools and Setting tool_choice

Picking up from Exercise 2: four well-described tools are registered. Now you decide **which
tools the agent sees** and **how it is allowed to choose** among them.

## What to build

The schema list the model receives (exactly the four scoped tools, nothing leaked), and the
`tool_choice` policy: forced single tool when sequencing matters, `any` when a structured call is
required, `auto` when the model should decide. A guard enforces that `check_stock` runs before
`process_return`.

## Where the TODOs are

- `inventory_agent/bridge.py` — `anthropic_tool_schemas` (returns one `{name, description,
  input_schema}` per registered tool). `list_tools()` is async; call it with `asyncio.run`.
- `inventory_agent/policy.py` — `tool_choice_for`, `build_messages_request`, and the
  `ReturnWorkflowGuard.record` / `can_run` methods. The `Workflow` taxonomy and
  `MAX_TOOLS_PER_AGENT` are given.

## Verify

```bash
.venv/bin/pytest tests/test_tool_distribution.py
```

This checks the agent is configured with exactly four tools (within the 4-5 guideline), no
out-of-scope tool leaks in, each `tool_choice` payload matches its workflow, and the guard blocks
`process_return` until a stock check is recorded.
