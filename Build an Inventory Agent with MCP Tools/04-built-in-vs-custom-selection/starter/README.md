# Exercise 4 — Selecting Built-in vs Custom Tools

Picking up from Exercise 3: the agent has four scoped tools and a `tool_choice` policy. The last
piece is a framework that decides, for a given task, **which tool is the right one** — a built-in
file tool, the custom inventory tools, or the Edit-fails fallback.

## What to build

A priority-ordered rule table that maps a task description to the narrowest correct tool. Domain
operations (stock, price, returns, shrinkage) must route to the custom inventory tools, never a
built-in. An Edit that cannot find a unique anchor falls back to Read + Write.

## Where the TODOs are

- `inventory_agent/selection.py` — the `_RULES` table and the default return in `select_tool`.
  Order the rules from most specific to most general so the first match wins. The decision guide
  in `docs/tool_selection_guide.md` is your reference.

## Verify

```bash
.venv/bin/pytest tests/test_tool_selection.py
# then the full project:
.venv/bin/pytest
```

The selection tests check that representative tasks route to the expected tool and that the
Edit-fails case falls back to Read + Write. The full suite (80 tests) confirms the complete
project, including the end-to-end agent transcript, still works.
