# Solution — Distributing Tools and Setting tool_choice

Project state after Exercise 3. `bridge.py` and `policy.py` are complete on top of the earlier
work. Only `selection.py` is still stubbed, for the final exercise.

## Verify

```bash
.venv/bin/pytest tests/test_tool_distribution.py
```

All distribution tests pass: exactly four well-formed tool schemas within the per-agent limit, no
out-of-scope tools, the correct `tool_choice` payload per workflow (forced / `any` / `auto`), and
the return-workflow guard enforcing `check_stock` before `process_return`.
