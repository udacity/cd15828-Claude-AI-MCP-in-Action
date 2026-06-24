# Tool-selection guide: built-in vs custom

An architect chooses the *type* of tool per task. Built-in tools handle codebase and file work;
the custom inventory MCP tools handle domain operations. Reaching for the wrong type — e.g.
Bash to grep, or a built-in where a domain tool is required — is a common reliability failure.

## Built-in tools

| Task type | Tool | Why |
|-----------|------|-----|
| Search file *contents* for a pattern (function name, error string, callers) | **Grep** | Content search across files |
| Find files by *name/path* pattern (e.g. `**/*.test.py`) | **Glob** | Path-pattern matching, not content |
| Read the full contents of a known file | **Read** | Load a specific file |
| Create a new file or overwrite one wholesale | **Write** | Full-file write |
| Make a targeted, in-place change at a unique anchor | **Edit** | Surgical edit by unique text match |
| Run a command / execute the suite | **Bash** | Execution |

### Edit-fails fallback

When **Edit** cannot find a unique anchor (the target text is not unique), do not force it.
Fall back to **Read + Write**: read the full file, modify the content in memory, and write it
back. This is the reliable path for non-unique modifications.

## When a custom inventory tool is required instead

Domain operations — checking stock, changing a price, processing a return, flagging shrinkage —
must use the custom inventory MCP tools (`check_stock`, `update_price`, `process_return`,
`flag_shrinkage`), never a built-in. A built-in like Grep over raw data files cannot enforce the
typed schemas, approval intercepts, or structured errors those operations require.

The decision is implemented in `inventory_agent/selection.py` (`select_tool`).
