"""FastMCP server exposing the four inventory tools.

Each tool is a thin wrapper over :class:`InventoryService`; its description comes from the
tool contract so descriptions stay the single source of truth. The handlers return the
camelCase wire form of :class:`ToolResult`.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from inventory_agent.contracts import CONTRACTS
from inventory_agent.service import InventoryService

EXPECTED_TOOLS = frozenset({"check_stock", "update_price", "process_return", "flag_shrinkage"})


def system_prompt() -> str:
    """Agent system prompt.

    Intentionally free of tool names and keyword->tool steering: tool selection must be driven
    by the tool descriptions, not by hard-wired instructions in the system prompt. Keyword-
    sensitive phrasing here would override well-written descriptions and cause misrouting.
    """
    return (
        "You are an inventory operations assistant for a multi-location retail chain. "
        "Help the user resolve stock, pricing, returns, and loss-prevention requests accurately. "
        "Choose the most appropriate available tool for each request based on the tool "
        "descriptions, and never guess values you can look up. If an action is blocked or fails, "
        "explain the reason and the recommended next step."
    )


def build_server(service: InventoryService | None = None) -> FastMCP:
    """Construct the MCP server with the four single-purpose inventory tools registered."""
    svc = service or InventoryService.from_file()
    server = FastMCP("retail-inventory")

    @server.tool(name="check_stock", description=CONTRACTS["check_stock"].render())
    def check_stock(sku: str, warehouse_id: str) -> dict[str, Any]:
        return svc.check_stock(sku, warehouse_id).to_wire()

    @server.tool(name="update_price", description=CONTRACTS["update_price"].render())
    def update_price(sku: str, new_price: float, manager_approved: bool) -> dict[str, Any]:
        return svc.update_price(sku, new_price, manager_approved).to_wire()

    @server.tool(name="process_return", description=CONTRACTS["process_return"].render())
    def process_return(sku: str, order_id: str, days_since_purchase: int) -> dict[str, Any]:
        return svc.process_return(sku, order_id, days_since_purchase).to_wire()

    @server.tool(name="flag_shrinkage", description=CONTRACTS["flag_shrinkage"].render())
    def flag_shrinkage(sku: str, warehouse_id: str, suspected_units: int) -> dict[str, Any]:
        return svc.flag_shrinkage(sku, warehouse_id, suspected_units).to_wire()

    return server
