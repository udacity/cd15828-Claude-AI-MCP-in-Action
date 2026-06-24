# Exercise 2 — Designing Differentiated Tool Descriptions

Picking up from Exercise 1: the error contract is in place and every handler returns a
`ToolResult`. Now you write the **tool descriptions** the agent reads to pick the right tool.

## What to build

Four single-purpose tools, each with a description that states its purpose, inputs, outputs, and
an explicit boundary. Two of the tools (`check_stock` and `process_return`) take the same product
id, so each one's "do not use for..." clause has to point at the other. That boundary clause is
what stops the agent from misrouting.

## Where the TODOs are

- `inventory_agent/contracts.py` — fill in all six fields for each of the four `CONTRACTS`
  entries. Keep each tool single-purpose. No catch-all "mode" tool.
- `inventory_agent/router.py` — `_INTENT_KEYWORDS`, in priority order, encoding the same
  boundaries you wrote in the contracts.

The MCP server (`server.py`) already registers exactly these four tools using your descriptions,
and `docs/monolithic_antipattern.md` explains why one god-tool was split into four.

## Verify

```bash
.venv/bin/pytest tests/test_tool_definitions.py
```

This checks there are exactly four tools, every description carries all its sections, the
`check_stock` / `process_return` descriptions disambiguate, the router resolves each intent, and
the system prompt has no keyword steering.
