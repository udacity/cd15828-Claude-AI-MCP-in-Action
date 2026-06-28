"""Four differentiated, single-purpose MCP tools.

Covers four typed tools, structured descriptions (with example +
edge case), disambiguation + router, no catch-all (decomposition doc),
and a system prompt free of keyword-sensitive steering.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from inventory_agent.contracts import CONTRACTS
from inventory_agent.router import route_intent
from inventory_agent.server import EXPECTED_TOOLS, build_server, system_prompt

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL_NAMES = ["check_stock", "flag_shrinkage", "process_return", "update_price"]


async def _tools() -> dict[str, object]:
    server = build_server()
    return {t.name: t for t in await server.list_tools()}


# --- Tool registration and typed schemas -------------------------------------------------------------------------


async def test_server_registers_exactly_four_named_tools() -> None:
    tools = await _tools()
    assert set(tools) == EXPECTED_TOOLS
    assert len(tools) == 4


async def test_every_tool_has_a_typed_input_schema() -> None:
    expected_props = {
        "check_stock": {"sku", "warehouse_id"},
        "update_price": {"sku", "new_price", "manager_approved"},
        "process_return": {"sku", "order_id", "days_since_purchase"},
        "flag_shrinkage": {"sku", "warehouse_id", "suspected_units"},
    }
    tools = await _tools()
    for name, props in expected_props.items():
        schema = tools[name].inputSchema  # type: ignore[attr-defined]
        assert schema["type"] == "object"
        assert props <= set(schema["properties"]), name
        assert schema.get("required"), name


async def test_every_tool_has_a_nonempty_description() -> None:
    tools = await _tools()
    for name, tool in tools.items():
        desc = tool.description  # type: ignore[attr-defined]
        assert desc and len(desc) > 40, name


# --- Structured tool descriptions -------------------------------------------------------------------------


@pytest.mark.parametrize("name", TOOL_NAMES)
def test_contract_has_all_structural_sections(name: str) -> None:
    c = CONTRACTS[name]
    assert c.purpose.strip()
    assert c.inputs.strip()
    assert c.outputs.strip()
    assert c.boundaries.strip()  # "do not use for ..."
    assert c.example_query.strip()
    assert c.edge_case.strip()


@pytest.mark.parametrize("name", TOOL_NAMES)
def test_rendered_description_surfaces_every_section(name: str) -> None:
    rendered = CONTRACTS[name].render().lower()
    for marker in ("purpose", "inputs", "outputs", "do not use", "example", "edge case"):
        assert marker in rendered, (name, marker)


# --- Disambiguation and intent routing -------------------------------------------------------------------------


def test_check_stock_and_process_return_descriptions_disambiguate() -> None:
    cs = CONTRACTS["check_stock"].render().lower()
    pr = CONTRACTS["process_return"].render().lower()
    # both accept a product id, so each must point away from the other by name
    assert "process_return" in cs
    assert "check_stock" in pr


@pytest.mark.parametrize(
    "intent,expected",
    [
        ("how many units of SKU-1001 are in stock in the east warehouse?", "check_stock"),
        ("is product SKU-1002 available right now", "check_stock"),
        ("customer wants to return SKU-1001 from order 55", "process_return"),
        ("process a refund / send-back for this item", "process_return"),
        ("change the price of SKU-1003 to 9.99", "update_price"),
        ("apply a markdown to this product", "update_price"),
        ("report suspected shrinkage / inventory loss for SKU-1004", "flag_shrinkage"),
        ("we think units went missing due to theft", "flag_shrinkage"),
    ],
)
def test_router_resolves_intent_to_correct_tool(intent: str, expected: str) -> None:
    assert route_intent(intent) == expected


# --- No generic catch-all tool -------------------------------------------------------------------------


async def test_no_generic_catchall_tool_is_registered() -> None:
    tools = await _tools()
    banned = {"manage_inventory", "inventory", "do_action", "execute", "run"}
    assert not (set(tools) & banned)
    # a monolithic tool would expose an action/mode/operation selector parameter
    for name, tool in tools.items():
        props = set(tool.inputSchema["properties"])  # type: ignore[attr-defined]
        assert not ({"action", "mode", "operation", "command"} & props), name


def test_decomposition_doc_documents_monolithic_antipattern() -> None:
    doc = (REPO_ROOT / "docs" / "monolithic_antipattern.md").read_text()
    assert "manage_inventory" in doc
    for tool in ("check_stock", "update_price", "process_return", "flag_shrinkage"):
        assert tool in doc


# --- System prompt steering -------------------------------------------------------------------------


def test_system_prompt_is_free_of_keyword_sensitive_steering() -> None:
    prompt = system_prompt().lower()
    # the system prompt must not name tools or hard-wire keyword->tool associations;
    # tool selection must be driven by the descriptions, not the system prompt.
    for tool in ("check_stock", "update_price", "process_return", "flag_shrinkage"):
        assert tool not in prompt
    for steer in ("always use", "whenever you see", "if the user says"):
        assert steer not in prompt
