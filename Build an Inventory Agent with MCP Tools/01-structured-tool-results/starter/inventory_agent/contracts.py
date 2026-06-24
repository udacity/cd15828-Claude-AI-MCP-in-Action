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


# TODO: Write a differentiated contract for each of the four single-purpose tools. Fill in every
# field with real text. The two tools that share a product-id input (check_stock and
# process_return) must each name the other in their `boundaries` ("do not use for...") so the
# agent never confuses a stock lookup with a return. Keep each tool single-purpose: no catch-all
# "mode" tool. Replace the empty strings below.
CONTRACTS: dict[str, ToolContract] = {
    "check_stock": ToolContract(
        name="check_stock",
        purpose="",
        inputs="",
        outputs="",
        boundaries="",
        example_query="",
        edge_case="",
    ),
    "update_price": ToolContract(
        name="update_price",
        purpose="",
        inputs="",
        outputs="",
        boundaries="",
        example_query="",
        edge_case="",
    ),
    "process_return": ToolContract(
        name="process_return",
        purpose="",
        inputs="",
        outputs="",
        boundaries="",
        example_query="",
        edge_case="",
    ),
    "flag_shrinkage": ToolContract(
        name="flag_shrinkage",
        purpose="",
        inputs="",
        outputs="",
        boundaries="",
        example_query="",
        edge_case="",
    ),
}
