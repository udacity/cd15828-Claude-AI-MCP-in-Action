# Solution — Selecting Built-in vs Custom Tools

Final project state. Every module is complete, and this `solution/` equals the reference
implementation (the differences across the chain were stub-to-implementation only). This final
stage holds the full working project.

## Verify

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest          # 80 passed
python3 -m inventory_agent # replay the end-to-end demo transcript (offline)
```

The full suite is green, including the end-to-end agent run: a stock check that recovers from a
transient timeout on retry, and an unapproved price change that is blocked and escalated. The
console-script test (`test_console_script_is_registered`) requires the editable install above; run
`pytest` from source without installing and that one test will be skipped/failing only because the
entry point is not registered yet.
