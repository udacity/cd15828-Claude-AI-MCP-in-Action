# Exercise 2 — Custom Servers, Tool Descriptions & a Schema Resource

Picking up from Exercise 1: the scoped config registry and CI gate are in place. The
registry declares two **custom** servers — now you build them, describe them so an agent
can't fall back to a generic built-in, and publish the claims schema as a Resource.

## What you'll build

- The **build-vs-reuse** decision engine that justifies *why* claims and policy are custom
  (proprietary, PII) while GitHub/Slack are community.
- The two custom servers' **tool descriptions**, engineered to beat the model's built-in
  default, plus the **linter** that scores them — the same bar the project dogfoods.
- The **schema Resource** (`claims://schema`) so agents discover fields without burning
  exploratory `get_claim` calls.

## Where you write code

- `mcp_governance/decision.py` — `decide` (the four build-vs-reuse rules, in priority
  order) and `lint_description` (score a description 0–3 for the three fallback-resistant
  qualities).
- `mcp_governance/contracts.py` — `CONTRACTS`: one `ToolContract` per tool, each carrying a
  *when to use*, an *instead of the built-in*, and an *example*. These must later pass the
  linter at full score.
- `mcp_governance/servers.py` — the structured `_not_found` error result (Graceful Tool
  Failure: return it, never raise) and the `claims://schema` resource registration.
- `mcp_governance/schema.py` — `build_schema_catalog`, derived from `CLAIMS_SCHEMA`.

> FastMCP and MCP Resources come from the `mcp` SDK (`from mcp.server.fastmcp import
> FastMCP`, `@server.tool`, `@server.resource(uri)`) — not the Anthropic cookbook.

## Run / verify

```bash
.venv/bin/pytest tests/test_servers.py tests/test_resource.py tests/test_decision.py
.venv/bin/mcp-governance decide                  # renders the five-need decision matrix
```
