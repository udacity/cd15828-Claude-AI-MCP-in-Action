"""Contract-based intent router.

A small, deterministic resolver that maps a natural-language intent to the single correct tool.
It exists to demonstrate that well-bounded tools can be disambiguated even when they share an
input shape (``check_stock`` and ``process_return`` both take a product id). Priority order
encodes the boundary clauses from the tool contracts.
"""

from __future__ import annotations

# TODO: Encode the boundary clauses from your tool contracts as keyword lists, in priority order
# (the first tool with a matching keyword wins). Order matters: more specific intents (shrinkage,
# returns, pricing) should be checked before the general stock-availability keywords so a phrase
# like "return this item" never resolves to check_stock.
_INTENT_KEYWORDS: list[tuple[str, tuple[str, ...]]] = []


def route_intent(intent: str) -> str | None:
    """Return the tool name that should handle ``intent``, or ``None`` if unmatched."""
    text = intent.lower()
    for tool, keywords in _INTENT_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return tool
    return None
