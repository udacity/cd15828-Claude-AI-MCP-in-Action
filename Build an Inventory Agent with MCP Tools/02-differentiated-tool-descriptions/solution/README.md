# Solution — Designing Differentiated Tool Descriptions

Project state after Exercise 2. `contracts.py` and `router.py` are complete on top of the
Exercise 1 work. `bridge`, `policy`, and `selection` are still stubbed for later exercises.

## Verify

```bash
.venv/bin/pytest tests/test_tool_definitions.py
```

All tool-definition tests pass: exactly four named tools, each with a typed input schema and a
full description, the shared-input tools disambiguated by their boundary clauses, the router
resolving intents, and a system prompt free of keyword-to-tool steering.
