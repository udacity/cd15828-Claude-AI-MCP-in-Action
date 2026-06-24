"""Tool contracts — the single source of truth for each tool's description.

A description is the primary mechanism an LLM uses to choose a tool. When two tools accept the
same input (``check_stock`` and ``process_return`` both take a product id), only an explicit
boundary clause keeps the agent from misrouting. Each contract therefore carries its purpose,
inputs, outputs, an explicit "do not use for" boundary, an example query, and an edge-case note.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContract:
    name: str
    purpose: str
    inputs: str
    outputs: str
    boundaries: str
    example_query: str
    edge_case: str

    def render(self) -> str:
        """Render the contract into the description string registered with the tool."""
        return (
            f"Purpose: {self.purpose}\n"
            f"Inputs: {self.inputs}\n"
            f"Outputs: {self.outputs}\n"
            f"Do NOT use for: {self.boundaries}\n"
            f"Example query: {self.example_query}\n"
            f"Edge case: {self.edge_case}"
        )


CONTRACTS: dict[str, ToolContract] = {
    "check_stock": ToolContract(
        name="check_stock",
        purpose="Read-only lookup of on-hand inventory quantity for one SKU at one warehouse.",
        inputs="sku (format SKU-#### ) and warehouse_id.",
        outputs="The available quantity and warehouse, with no side effects.",
        boundaries=(
            "processing a return or any write. It only reads availability; to take back "
            "merchandise use process_return. A zero result means in stock = 0, not an error."
        ),
        example_query="How many units of SKU-1001 are on hand in the east warehouse?",
        edge_case=(
            "A SKU that exists but has zero units returns quantity 0 (a valid, successful answer)."
        ),
    ),
    "update_price": ToolContract(
        name="update_price",
        purpose=(
            "Change the selling price of one SKU. This is a write that requires manager approval."
        ),
        inputs="sku, new_price (positive), and manager_approved (boolean).",
        outputs="The SKU's previous and new price after a successful, approved change.",
        boundaries=(
            "reading prices or stock. It mutates pricing; without manager_approved it is "
            "blocked before any change is made."
        ),
        example_query="Change the price of SKU-1003 to 9.99 (approved by the store manager).",
        edge_case=(
            "Without manager approval the price is never changed; a permission error is returned."
        ),
    ),
    "process_return": ToolContract(
        name="process_return",
        purpose="Authorize return merchandise (RMA) for a previously purchased SKU.",
        inputs="sku, order_id, and days_since_purchase.",
        outputs="An RMA authorization id when the item is inside its return window.",
        boundaries=(
            "checking availability. It does not read stock levels; to ask how many units are "
            "on hand use check_stock. Returns outside the window are rejected as a business error."
        ),
        example_query="A customer wants to return SKU-1001 from order 55, purchased 10 days ago.",
        edge_case=(
            "If days_since_purchase exceeds the SKU's return window, the return is refused "
            "(business rule)."
        ),
    ),
    "flag_shrinkage": ToolContract(
        name="flag_shrinkage",
        purpose="Open a loss-prevention case for suspected inventory shrinkage at a warehouse.",
        inputs="sku, warehouse_id, and suspected_units (positive integer).",
        outputs="A shrinkage case id recording the report.",
        boundaries=(
            "adjusting stock or price. It records a suspected-loss report only; it does not "
            "change inventory counts."
        ),
        example_query="Report 4 suspected missing units of SKU-1004 at the west warehouse.",
        edge_case=(
            "suspected_units must be a positive integer; zero or negative is a validation error."
        ),
    ),
}
