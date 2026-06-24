"""Bridge between the MCP tool layer and the Anthropic Messages API.

Two conversions live here:

* :func:`anthropic_tool_schemas` turns the MCP server's registered tools into the
  ``{name, description, input_schema}`` shape the Messages API expects — so the tool
  descriptions and schemas have a single source of truth (the MCP server).
* :func:`to_tool_result_block` maps a :class:`ToolResult` (MCP camelCase ``isError``) into a
  Messages API ``tool_result`` content block (snake_case ``is_error``).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from inventory_agent.errors import ToolResult


def anthropic_tool_schemas(server: FastMCP) -> list[dict[str, Any]]:
    """Convert the MCP server's tools into Anthropic Messages API tool schemas."""
    tools = asyncio.run(server.list_tools())
    return [
        {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
        for t in tools
    ]


def to_tool_result_block(tool_use_id: str, result: ToolResult) -> dict[str, Any]:
    """Build a Messages API ``tool_result`` content block from a :class:`ToolResult`.

    The MCP layer uses camelCase ``isError``; the Messages API block uses snake_case
    ``is_error``. The full structured envelope is serialized as the block's text content so the
    agent sees the category and retryability.
    """
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "is_error": result.is_error,
        "content": json.dumps(result.to_wire()),
    }
