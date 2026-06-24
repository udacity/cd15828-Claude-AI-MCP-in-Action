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
        if not _SKU_PATTERN.match(sku):
            return None, ToolResult.fail(
                ErrorCategory.VALIDATION, f"Malformed SKU '{sku}'; expected format SKU-####."
            )
        product = self._products.get(sku)
        if product is None:
            return None, ToolResult.fail(ErrorCategory.VALIDATION, f"Unknown SKU '{sku}'.")
        return product, None

    def _check_warehouse(self, warehouse_id: str) -> ToolResult | None:
        """Return a validation error if the warehouse id is unknown, else None."""
        if warehouse_id not in self._warehouses:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, f"Unknown warehouse '{warehouse_id}'."
            )
        return None

    # -- tool handlers -----------------------------------------------------------------

    def check_stock(self, sku: str, warehouse_id: str) -> ToolResult:
        product, error = self._resolve_product(sku)
        if error is not None:
            return error
        if (wh_error := self._check_warehouse(warehouse_id)) is not None:
            return wh_error
        if self._warehouses[warehouse_id]["status"] != "online":
            return ToolResult.fail(
                ErrorCategory.TRANSIENT,
                f"Warehouse '{warehouse_id}' API timed out; the warehouse is unreachable.",
            )
        assert product is not None
        quantity = product["stock"].get(warehouse_id, 0)
        return ToolResult.ok({"sku": sku, "warehouse_id": warehouse_id, "quantity": quantity})

    def update_price(self, sku: str, new_price: float, manager_approved: bool) -> ToolResult:
        product, error = self._resolve_product(sku)
        if error is not None:
            return error
        if new_price <= 0:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, f"new_price must be positive; got {new_price}."
            )
        # Application-layer intercept: block the mutation before it happens. The price is never
        # changed without manager approval, regardless of how the request is phrased.
        if not manager_approved:
            return ToolResult.fail(
                ErrorCategory.PERMISSION,
                f"Price change for {sku} requires manager approval; no change was made.",
            )
        assert product is not None
        previous = product["price"]
        product["price"] = new_price
        return ToolResult.ok({"sku": sku, "previous_price": previous, "new_price": new_price})

    def process_return(self, sku: str, order_id: str, days_since_purchase: int) -> ToolResult:
        product, error = self._resolve_product(sku)
        if error is not None:
            return error
        if days_since_purchase < 0:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, "days_since_purchase must be non-negative."
            )
        assert product is not None
        window = product["return_window_days"]
        if days_since_purchase > window:
            return ToolResult.fail(
                ErrorCategory.BUSINESS,
                f"Return window of {window} days expired "
                f"({days_since_purchase} days since purchase).",
            )
        rma_id = f"RMA-{order_id}-{sku}"
        return ToolResult.ok({"sku": sku, "order_id": order_id, "rma_id": rma_id})

    def flag_shrinkage(self, sku: str, warehouse_id: str, suspected_units: int) -> ToolResult:
        _, error = self._resolve_product(sku)
        if error is not None:
            return error
        if (wh_error := self._check_warehouse(warehouse_id)) is not None:
            return wh_error
        if suspected_units <= 0:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, "suspected_units must be a positive integer."
            )
        return ToolResult.ok(
            {
                "sku": sku,
                "warehouse_id": warehouse_id,
                "suspected_units": suspected_units,
                "case_id": f"SHRINK-{warehouse_id}-{sku}",
            }
        )
