"""Generate the demo transcript fixture against the real Anthropic API.

Run once to (re)create ``fixtures/demo_transcript.json``. Requires ANTHROPIC_API_KEY in the
environment. The committed transcript is what the test suite and CLI replay offline.

    ANTHROPIC_API_KEY=... python scripts/generate_fixture.py
"""

from __future__ import annotations

import json
from pathlib import Path

from anthropic import Anthropic

from inventory_agent.agent import DEFAULT_MODEL, generate_demo_transcript

OUTPUT = Path(__file__).resolve().parent.parent / "fixtures" / "demo_transcript.json"


def main() -> int:
    client = Anthropic()
    transcript = generate_demo_transcript(client, DEFAULT_MODEL)
    OUTPUT.write_text(json.dumps(transcript, indent=2) + "\n")
    print(f"Wrote {OUTPUT} with {len(transcript['events'])} events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
