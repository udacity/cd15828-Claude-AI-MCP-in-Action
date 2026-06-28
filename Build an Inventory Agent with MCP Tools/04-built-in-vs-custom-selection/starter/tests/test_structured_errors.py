"""Structured error responses with categories.

Covers the uniform isError envelope; all four categories (permission
is a pre-mutation intercept); only transient is retryable; an empty result is
not an error; and no generic/unstructured errors (nothing raises).
"""

from __future__ import annotations

import pytest

from inventory_agent.errors import ErrorCategory, ToolResult
from inventory_agent.service import InventoryService


@pytest.fixture
def svc() -> InventoryService:
    return InventoryService.from_file()


# --- Uniform envelope + wire shape ------------------------------------------


def test_success_wire_shape_has_isError_false_and_data() -> None:
    wire = ToolResult.ok({"quantity": 3}).to_wire()
    assert wire["isError"] is False
    assert wire["data"] == {"quantity": 3}
    assert "errorCategory" not in wire  # success carries no error fields


def test_error_wire_shape_uses_camelcase_fields() -> None:
    wire = ToolResult.fail(ErrorCategory.VALIDATION, "bad sku").to_wire()
    assert wire["isError"] is True
    assert wire["errorCategory"] == "validation"
    assert wire["isRetryable"] is False
    assert wire["message"] == "bad sku"


# --- Each category exercised by a real tool ---------------------------------


def test_transient_error_on_offline_warehouse(svc: InventoryService) -> None:
    res = svc.check_stock("SKU-1001", "WH-SOUTH")  # WH-SOUTH is offline in the dataset
    assert res.is_error and res.error_category is ErrorCategory.TRANSIENT


def test_validation_error_on_malformed_sku(svc: InventoryService) -> None:
    res = svc.check_stock("not-a-sku", "WH-EAST")
    assert res.is_error and res.error_category is ErrorCategory.VALIDATION


def test_business_error_when_return_window_expired(svc: InventoryService) -> None:
    res = svc.process_return("SKU-1003", "ORD-9", days_since_purchase=60)  # window is 14
    assert res.is_error and res.error_category is ErrorCategory.BUSINESS


def test_permission_error_when_price_change_unapproved(svc: InventoryService) -> None:
    res = svc.update_price("SKU-1003", 5.00, manager_approved=False)
    assert res.is_error and res.error_category is ErrorCategory.PERMISSION


def test_permission_intercept_blocks_mutation_before_execution(svc: InventoryService) -> None:
    # An unapproved change must NOT alter the price. Prove it: a later approved change still
    # reports the ORIGINAL price (19.99) as previous_price, not the blocked value (5.00).
    blocked = svc.update_price("SKU-1003", 5.00, manager_approved=False)
    assert blocked.is_error
    approved = svc.update_price("SKU-1003", 9.99, manager_approved=True)
    assert approved.data is not None
    assert approved.data["previous_price"] == 19.99


# --- Retryability ------------------------------------------------------------


@pytest.mark.parametrize(
    "category,expected",
    [
        (ErrorCategory.TRANSIENT, True),
        (ErrorCategory.VALIDATION, False),
        (ErrorCategory.BUSINESS, False),
        (ErrorCategory.PERMISSION, False),
    ],
)
def test_only_transient_is_retryable(category: ErrorCategory, expected: bool) -> None:
    assert ToolResult.fail(category, "x").is_retryable is expected


# --- Empty result is not an error -------------------------------------------


def test_zero_stock_is_a_successful_empty_result(svc: InventoryService) -> None:
    res = svc.check_stock("SKU-1001", "WH-WEST")  # WH-WEST has 0 units of SKU-1001
    assert res.is_error is False
    assert res.data is not None and res.data["quantity"] == 0


def test_empty_result_is_distinguishable_from_transient_failure(svc: InventoryService) -> None:
    empty = svc.check_stock("SKU-1001", "WH-WEST")
    unreachable = svc.check_stock("SKU-1001", "WH-SOUTH")
    assert empty.is_error is False
    assert unreachable.is_error is True
    assert empty.to_wire() != unreachable.to_wire()


# --- No generic/unstructured errors; nothing raises -------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.check_stock("bad", "WH-EAST"),
        lambda s: s.check_stock("SKU-9999", "WH-EAST"),
        lambda s: s.check_stock("SKU-1001", "WH-NOPE"),
        lambda s: s.update_price("bad", 5.0, True),
        lambda s: s.update_price("SKU-1003", -1.0, True),
        lambda s: s.update_price("SKU-1003", 5.0, False),
        lambda s: s.process_return("bad", "O1", 1),
        lambda s: s.process_return("SKU-1003", "O1", 60),
        lambda s: s.flag_shrinkage("bad", "WH-EAST", 1),
        lambda s: s.flag_shrinkage("SKU-1004", "WH-EAST", 0),
    ],
)
def test_every_error_path_returns_typed_result_and_never_raises(
    svc: InventoryService, call: object
) -> None:
    result = call(svc)  # type: ignore[operator]
    assert isinstance(result, ToolResult)
    assert result.is_error is True
    assert result.error_category in set(ErrorCategory)
    assert result.message  # human-readable, never an empty/generic blank
