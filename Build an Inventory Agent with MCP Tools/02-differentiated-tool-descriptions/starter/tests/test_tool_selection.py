"""Built-in vs custom tool-selection framework.

Covers the selection guide doc and select_tool (incl. Edit-fails fallback).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from inventory_agent.selection import CUSTOM_INVENTORY, select_tool

GUIDE = Path(__file__).resolve().parent.parent / "docs" / "tool_selection_guide.md"


# --- Selection guide doc -------------------------------------------------------------------------


def test_selection_guide_covers_all_builtins_fallback_and_custom() -> None:
    doc = GUIDE.read_text()
    for builtin in ("Grep", "Glob", "Read", "Write", "Edit", "Bash"):
        assert builtin in doc
    assert "Read + Write" in doc  # Edit-fails fallback
    assert "custom inventory" in doc.lower()


# --- select_tool routing -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "task,expected",
    [
        ("search the codebase for all callers of process_order", "Grep"),
        ("find every file matching **/*.test.py", "Glob"),
        ("read the full contents of config/settings.toml", "Read"),
        ("create a new module file from scratch", "Write"),
        ("make a targeted, in-place edit to the import line", "Edit"),
        ("run the test suite via the shell", "Bash"),
        ("Edit failed: the anchor text is not unique, so modify the file safely", "Read+Write"),
        ("check how many units of SKU-1001 are in stock", CUSTOM_INVENTORY),
        ("process a customer return for order 5", CUSTOM_INVENTORY),
        ("update the price of an item", CUSTOM_INVENTORY),
    ],
)
def test_select_tool_routes_task_to_correct_tool(task: str, expected: str) -> None:
    assert select_tool(task) == expected


def test_edit_fails_fallback_is_read_plus_write() -> None:
    assert select_tool("the Edit anchor is not unique") == "Read+Write"
