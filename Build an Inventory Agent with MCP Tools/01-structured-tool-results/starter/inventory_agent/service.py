"""Inventory domain service.

Pure, synchronous business logic over a local inventory dataset. Every public method returns
a :class:`ToolResult`; no exception crosses the method boundary. The MCP server (see
:mod:`inventory_agent.server`) wraps these methods as tools.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from inventory_agent.errors import ErrorCategory, ToolResult

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.json"

_SKU_PATTERN = re.compile(r"^SKU-\d{4}$")


class InventoryService:
    """In-memory inventory state loaded from a JSON dataset."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._warehouses: dict[str, Any] = data["warehouses"]
        self._products: dict[str, Any] = data["products"]

    @classmethod
    def from_file(cls, path: Path | None = None) -> InventoryService:
        raw = json.loads((path or DEFAULT_DATA_PATH).read_text())
        return cls(raw)

    # -- validation helpers ------------------------------------------------------------

    def _resolve_product(self, sku: str) -> tuple[dict[str, Any] | None, ToolResult | None]:
        """Return (product, None) or (None, validation_error)."""
        # TODO: A malformed SKU and an unknown SKU are both VALIDATION failures. Return a
        # (None, ToolResult.fail(...)) pair for each, or (product, None) when the SKU resolves.
        raise NotImplementedError

    def _check_warehouse(self, warehouse_id: str) -> ToolResult | None:
        """Return a validation error if the warehouse id is unknown, else None."""
        # TODO: An unknown warehouse id is a VALIDATION failure; a known one returns None.
        raise NotImplementedError

    # -- tool handlers -----------------------------------------------------------------

    def check_stock(self, sku: str, warehouse_id: str) -> ToolResult:
        # TODO: Read-only lookup. Validate the SKU and warehouse, treat an offline warehouse as
        # a TRANSIENT failure, and return ToolResult.ok with the quantity. A SKU with zero units
        # is a SUCCESS with quantity 0, not an error.
        raise NotImplementedError

    def update_price(self, sku: str, new_price: float, manager_approved: bool) -> ToolResult:
        # TODO: A non-positive price is VALIDATION. Without manager approval, block the mutation
        # BEFORE changing anything and return a PERMISSION failure. Only mutate once approved,
        # then return ToolResult.ok with previous and new price.
        raise NotImplementedError

    def process_return(self, sku: str, order_id: str, days_since_purchase: int) -> ToolResult:
        # TODO: Negative days is VALIDATION. A return past the SKU's return window is a BUSINESS
        # failure (a valid request the business rejects). Otherwise return ToolResult.ok with an
        # RMA id.
        raise NotImplementedError

    def flag_shrinkage(self, sku: str, warehouse_id: str, suspected_units: int) -> ToolResult:
        # TODO: Validate the SKU and warehouse. suspected_units must be a positive integer
        # (VALIDATION otherwise). Return ToolResult.ok with a shrinkage case id.
        raise NotImplementedError
