"""CLI entry point.

Replays the committed demo transcript (no network), so the end-to-end scenario can be
demonstrated offline. The transcript itself is generated against the real API by
``scripts/generate_fixture.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "demo_transcript.json"


def _format_event(event: dict[str, Any]) -> str:
    kind = event["type"]
    if kind == "user":
        return f"USER: {event['text']}"
    if kind == "assistant":
        return f"ASSISTANT: {event['text']}"
    if kind == "tool_use":
        return f"  -> call {event['name']}(attempt {event['attempt']}) {json.dumps(event['input'])}"
    if kind == "tool_result":
        if event.get("isError"):
            return (
                f"  <- {event['name']} ERROR [{event.get('errorCategory')}] "
                f"retryable={event.get('isRetryable')}: {event.get('message')}"
            )
        return f"  <- {event['name']} ok {json.dumps(event.get('data', {}))}"
    if kind == "escalation":
        return f"  !! ESCALATION {json.dumps(event['payload'])}"
    return json.dumps(event)


def main() -> int:
    transcript = json.loads(FIXTURE_PATH.read_text())
    print(f"Replaying demo transcript ({transcript['scenario']}, model {transcript['model']}):\n")
    for event in transcript["events"]:
        print(_format_event(event))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
