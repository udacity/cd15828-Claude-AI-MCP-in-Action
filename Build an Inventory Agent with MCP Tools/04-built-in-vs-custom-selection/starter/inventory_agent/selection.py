"""Built-in vs custom tool-selection framework.

Maps a task description to the correct tool. Built-in tools (Grep, Glob, Read, Write, Edit,
Bash) handle codebase/file work; the custom inventory MCP tools handle domain operations. The
framework also encodes the Edit-fails fallback: when Edit cannot find a unique anchor, the
reliable choice is Read + Write.
"""

from __future__ import annotations

CUSTOM_INVENTORY = "<custom inventory tool>"

# TODO: Build the priority-ordered rule table that maps a task to the narrowest correct tool.
# Each rule is (tool, keywords); the first matching rule wins, so order from most specific to
# most general. Cover: domain operations -> CUSTOM_INVENTORY; an Edit with no unique anchor ->
# "Read+Write"; plus Glob, Grep, Bash, Write, Edit, Read for file/codebase work.
_RULES: list[tuple[str, tuple[str, ...]]] = []


def select_tool(task: str) -> str:
    """Return the tool best suited to ``task``.

    Returns a built-in tool name (``Grep``/``Glob``/``Read``/``Write``/``Edit``/``Bash``),
    the ``Read+Write`` fallback, or :data:`CUSTOM_INVENTORY` for domain operations.
    """
    text = task.lower()
    for tool, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return tool
    # TODO: Choose a safe default tool when no rule matches (the most read-only, least
    # destructive option).
    raise NotImplementedError
