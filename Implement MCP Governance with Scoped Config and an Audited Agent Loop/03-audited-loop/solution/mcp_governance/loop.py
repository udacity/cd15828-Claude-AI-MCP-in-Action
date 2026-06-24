"""The guarded agent loop.

The model runs through a :class:`ModelRunner` Protocol so the real Anthropic client and a
scripted test double are interchangeable (no mocks at the API boundary -- the real path
makes real calls; the fake is a double for the *loop*, not a fake HTTP response). Every
tool call is dispatched through the :class:`~mcp_governance.audit.AuditedToolRunner` gateway,
so it lands in the audit trail. Termination is driven by ``stop_reason`` (exam Task 1.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from mcp_governance.audit import AuditedToolRunner, AuditTrail, Clock, SystemClock
from mcp_governance.bridge import Bridge
from mcp_governance.config import DEFAULT_MODEL

SYSTEM_PROMPT = (
    "You are a claims operations assistant for Northwind Mutual, a property and casualty "
    "insurer. Answer questions about claims and policies accurately. Choose the most "
    "appropriate available tool for each request based on the tool descriptions, and never "
    "guess values you can look up. If a lookup fails, explain why and the recommended next "
    "step. Do not fabricate claim or policy data."
)

MAX_ITERATIONS = 8  # runaway backstop only; real termination is stop_reason == "end_turn"


class ModelRunner(Protocol):
    def create(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Any: ...


class AnthropicRunner:
    """Real Anthropic client. Temperature 0 for reproducibility."""

    def __init__(self, client: Any = None, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client = client
        self._model = model

    def create(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Any:
        return self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0,
            system=system,
            tools=tools,
            messages=messages,
        )


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    name: str
    input: dict[str, Any]
    id: str
    type: str = "tool_use"


@dataclass
class ScriptedResponse:
    stop_reason: str
    content: list[Any] = field(default_factory=list)


class ScriptedRunner:
    """Returns pre-scripted responses in order -- a double for the loop, used to prove the
    enforcement is deterministic regardless of what the model attempts."""

    def __init__(self, responses: list[ScriptedResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def create(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ScriptedResponse:
        response = self._responses[self.calls]
        self.calls += 1
        return response


class Outcome(BaseModel):
    stop_reason: str
    final_text: str
    tool_calls: list[str]
    audit_entries: int


def _content_to_wire(content: list[Any]) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            wire.append({"type": "text", "text": block.text})
        elif getattr(block, "type", None) == "tool_use":
            wire.append(
                {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
            )
    return wire


def run_agent(
    *,
    request: str,
    runner: ModelRunner,
    bridge: Bridge,
    trail: AuditTrail,
    clock: Clock | None = None,
    caller_identity: str = "unknown",
    system_prompt: str = SYSTEM_PROMPT,
    max_iterations: int = MAX_ITERATIONS,
) -> Outcome:
    """Drive the model until it stops requesting tools. Returns a typed outcome."""
    gateway = AuditedToolRunner(bridge, trail, clock or SystemClock(), caller_identity)
    tools = bridge.anthropic_tools()
    messages: list[dict[str, Any]] = [{"role": "user", "content": request}]
    tool_calls: list[str] = []

    for _ in range(max_iterations):
        response = runner.create(system=system_prompt, messages=messages, tools=tools)
        if response.stop_reason != "tool_use":
            final_text = "".join(
                b.text for b in response.content if getattr(b, "type", None) == "text"
            )
            return Outcome(
                stop_reason=response.stop_reason,
                final_text=final_text,
                tool_calls=tool_calls,
                audit_entries=len(trail),
            )

        messages.append({"role": "assistant", "content": _content_to_wire(response.content)})
        results: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                tool_calls.append(block.name)
                result = gateway.run(block.name, dict(block.input))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                        "is_error": bool(result.get("is_error")),
                    }
                )
        messages.append({"role": "user", "content": results})

    # Backstop only: a well-behaved model terminates on end_turn well before this.
    return Outcome(
        stop_reason="max_iterations",
        final_text="",
        tool_calls=tool_calls,
        audit_entries=len(trail),
    )
