# Solution — Returning Structured Tool Results

Project state after Exercise 1. `errors.py`, `service.py`, and `escalation.py` are complete; the
later modules (`contracts`, `router`, `bridge`, `policy`, `selection`) are still stubbed and are
finished in later exercises.

## Verify

```bash
.venv/bin/pip install -e ".[dev]"   # if not already installed
.venv/bin/pytest tests/test_structured_errors.py
```

All structured-error tests pass: success vs. each error category, zero-stock as a successful
empty result, the permission intercept blocking the mutation, and only transient errors marked
retryable.
