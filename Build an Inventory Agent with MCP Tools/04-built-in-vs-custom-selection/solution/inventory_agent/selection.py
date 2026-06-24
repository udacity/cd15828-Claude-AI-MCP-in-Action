"""Built-in vs custom tool-selection framework.

Maps a task description to the correct tool. Built-in tools (Grep, Glob, Read, Write, Edit,
Bash) handle codebase/file work; the custom inventory MCP tools handle domain operations. The
framework also encodes the Edit-fails fallback: when Edit cannot find a unique anchor, the
reliable choice is Read + Write.
"""

from __future__ import annotations

CUSTOM_INVENTORY = "<custom inventory tool>"

# Checked in priority order; the first matching rule wins.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    # Domain operations require the custom MCP inventory tools, never a built-in.
    (CUSTOM_INVENTORY, ("stock", "inventory level", "price", "return", "refund", "shrinkage")),
    # Edit cannot find a unique anchor -> fall back to Read + Write.
    ("Read+Write", ("not unique", "no unique", "ambiguous anchor")),
    ("Glob", ("matching", "by name pattern", "extension", "glob", "*.")),
    ("Grep", ("search", "grep", "callers", "find all", "occurrences", "where is")),
    ("Bash", ("run ", "execute", "shell", "command", "invoke the cli")),
    ("Write", ("create", "overwrite", "new file", "from scratch", "write a new")),
    ("Edit", ("edit", "targeted", "in-place", "modify a line", "replace the line")),
    ("Read", ("read", "open", "view", "contents of", "inspect the file")),
]


def select_tool(task: str) -> str:
    """Return the tool best suited to ``task``.

    Returns a built-in tool name (``Grep``/``Glob``/``Read``/``Write``/``Edit``/``Bash``),
    the ``Read+Write`` fallback, or :data:`CUSTOM_INVENTORY` for domain operations.
    """
    text = task.lower()
    for tool, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return tool
    return "Read"
