"""End-to-end inventory agent loop over the Anthropic Messages API.

The loop drives real tool use: the model selects tools (via the descriptions and tool_choice
policy), and the harness executes them against the inventory service. Two recovery behaviors are
owned by the harness, not the model:

* **Auto-retry** transient errors up to a cap (Playbook: transient failures resolve in 2-3
  attempts).
* **Fail fast** on a permission error — halt the workflow and emit a structured escalation.

Every step is recorded into a transcript so a run can be captured as a fixture and replayed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from anthropic import Anthropic

from inventory_agent.bridge import to_tool_result_block
from inventory_agent.errors import ErrorCategory, ToolResult
from inventory_agent.escalation import build_escalation
from inventory_agent.policy import (
    ReturnWorkflowGuard,
    Workflow,
    build_messages_request,
)
from inventory_agent.server import build_server
from inventory_agent.service import InventoryService

MAX_TRANSIENT_RETRIES = 2
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def should_retry(result: ToolResult) -> bool:
    """A transient, retryable failure should be retried by the harness."""
    return bool(result.is_error and result.is_retryable)


def is_halting(result: ToolResult) -> bool:
    """A permission failure halts the workflow (fail fast)."""
    return result.is_error and result.error_category is ErrorCategory.PERMISSION


def _dispatch(service: InventoryService, name: str, args: dict[str, Any]) -> ToolResult:
    handlers: dict[str, Callable[..., ToolResult]] = {
        "check_stock": service.check_stock,
        "update_price": service.update_price,
        "process_return": service.process_return,
        "flag_shrinkage": service.flag_shrinkage,
    }
    return handlers[name](**args)


def _execute_with_retry(
    service: InventoryService,
    name: str,
    args: dict[str, Any],
    transcript: list[dict[str, Any]],
) -> ToolResult:
    """Execute a tool, auto-retrying transient failures up to the cap."""
    attempt = 0
    while True:
        attempt += 1
        transcript.append({"type": "tool_use", "name": name, "input": args, "attempt": attempt})
        result = _dispatch(service, name, args)
        transcript.append(
            {"type": "tool_result", "name": name, "attempt": attempt, **result.to_wire()}
        )
        if should_retry(result) and attempt <= MAX_TRANSIENT_RETRIES:
            continue
        return result


class FlakyInventoryService(InventoryService):
    """Inventory service whose first stock check per (sku, warehouse) times out transiently.

    Used only for demo/fixture generation so the captured transcript exercises the auto-retry
    recovery path deterministically.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self._flaked: set[tuple[str, str]] = set()

    def check_stock(self, sku: str, warehouse_id: str) -> ToolResult:
        key = (sku, warehouse_id)
        if key not in self._flaked:
            self._flaked.add(key)
            return ToolResult.fail(
                ErrorCategory.TRANSIENT,
                f"Warehouse '{warehouse_id}' API timed out; retry shortly.",
            )
        return super().check_stock(sku, warehouse_id)


def _content_to_dicts(content: Any) -> list[dict[str, Any]]:
    """Normalize SDK content blocks into plain dicts for the messages history."""
    blocks: list[dict[str, Any]] = []
    for block in content:
        if block.type == "text":
            blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            blocks.append(
                {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
            )
    return blocks


def run_phase(
    client: Anthropic,
    service: InventoryService,
    server: Any,
    transcript: list[dict[str, Any]],
    user_text: str,
    workflow: Workflow,
    model: str,
    guard: ReturnWorkflowGuard,
) -> bool:
    """Run one conversational phase. Returns True if the workflow halted on a permission error."""
    transcript.append({"type": "user", "text": user_text})
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]
    request = build_messages_request(model, messages, server, workflow)

    while True:
        response = client.messages.create(**request)
        messages.append({"role": "assistant", "content": _content_to_dicts(response.content)})
        for block in response.content:
            if block.type == "text" and block.text.strip():
                transcript.append({"type": "assistant", "text": block.text.strip()})

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_uses:
            return False

        tool_result_blocks: list[dict[str, Any]] = []
        for tu in tool_uses:
            args = dict(tu.input)
            result = _execute_with_retry(service, tu.name, args, transcript)
            guard.record(tu.name)
            tool_result_blocks.append(to_tool_result_block(tu.id, result))
            if is_halting(result):
                escalation = build_escalation(
                    sku=str(args.get("sku", "unknown")),
                    requested_change=f"{tu.name}({args})",
                    root_cause=result.message or "permission denied",
                )
                transcript.append({"type": "escalation", "payload": escalation.model_dump()})
                return True

        messages.append({"role": "user", "content": tool_result_blocks})
        # After the first steered turn, let the model decide whether more tools are needed.
        request = build_messages_request(model, messages, server, Workflow.OPEN_ENDED)


def generate_demo_transcript(client: Anthropic, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Drive the two-phase demo scenario against a real client and return the transcript.

    Phase A: a stock check that times out once and recovers on retry.
    Phase B: an unapproved price change that is blocked, halting with an escalation.
    """
    service = FlakyInventoryService.from_file()
    server = build_server(InventoryService.from_file())
    guard = ReturnWorkflowGuard()
    transcript: list[dict[str, Any]] = []

    run_phase(
        client,
        service,
        server,
        transcript,
        "How many units of SKU-1001 are on hand in the WH-EAST warehouse?",
        Workflow.GUARANTEED_TOOL,
        model,
        guard,
    )
    run_phase(
        client,
        service,
        server,
        transcript,
        (
            "I am a sales clerk without manager approval. Please change the price of SKU-1001 "
            "to 69.99."
        ),
        Workflow.GUARANTEED_TOOL,
        model,
        guard,
    )
    return {"model": model, "scenario": "retail-inventory-demo", "events": transcript}
