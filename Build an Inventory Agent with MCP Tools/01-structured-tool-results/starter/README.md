# Exercise 1 — Returning Structured Tool Results

This is the bootstrap scaffold for the whole project. The packaging, dataset, fixtures, tests,
the MCP server, and the agent loop are all here for you. Your job in this exercise is the **error
contract** every tool will return.

## Setup (once)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## What to build

Make every tool return one uniform result envelope instead of raising exceptions or returning
loose strings. The category on a failure is what lets an agent decide whether to retry, stop, or
escalate.

## Where the TODOs are

- `inventory_agent/errors.py` — `_RETRYABLE`, and the `ToolResult.ok`, `ToolResult.fail`, and
  `to_wire` bodies. The `ErrorCategory` taxonomy is given.
- `inventory_agent/service.py` — `_resolve_product`, `_check_warehouse`, and the four handler
  bodies (`check_stock`, `update_price`, `process_return`, `flag_shrinkage`). Each handler maps
  its failure to the right category and never raises.
- `inventory_agent/escalation.py` — `build_escalation`.

Two things to get right: a zero-stock result is a **success** (quantity 0), not an error; and an
unapproved price change must be blocked **before** any mutation, returned as a permission failure.

## Verify

```bash
.venv/bin/pytest tests/test_structured_errors.py
```

When that file is green, this stage is done. The other test files cover later exercises and will
not pass yet.
