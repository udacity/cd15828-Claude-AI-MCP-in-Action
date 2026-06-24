"""Structured tool-result contract shared by every inventory tool.

The serialized JSON uses the MCP camelCase convention (``isError``, ``errorCategory``,
``isRetryable``) so it reads identically on the wire to the MCP protocol. Python attributes
stay snake_case. The agent/bridge layer (see :mod:`inventory_agent.bridge`) maps ``isError``
to the Anthropic Messages API's snake_case ``is_error`` tool_result field.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorCategory(StrEnum):
    """MCP error categories that drive an agent's recovery decision."""

    TRANSIENT = "transient"
    VALIDATION = "validation"
    BUSINESS = "business"
    PERMISSION = "permission"


# Only transient failures are worth retrying; everything else is terminal for the agent.
_RETRYABLE = {ErrorCategory.TRANSIENT}


class ToolResult(BaseModel):
    """Uniform result envelope returned by every tool handler.

    Success: ``is_error`` is False and ``data`` carries the pruned payload.
    Failure: ``is_error`` is True with a populated category, retryability and message.
    """

    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)

    is_error: bool = Field(serialization_alias="isError")
    data: dict[str, Any] | None = Field(default=None)
    error_category: ErrorCategory | None = Field(default=None, serialization_alias="errorCategory")
    is_retryable: bool | None = Field(default=None, serialization_alias="isRetryable")
    message: str | None = Field(default=None)

    @classmethod
    def ok(cls, data: dict[str, Any]) -> ToolResult:
        return cls(is_error=False, data=data)

    @classmethod
    def fail(cls, category: ErrorCategory, message: str) -> ToolResult:
        return cls(
            is_error=True,
            error_category=category,
            is_retryable=category in _RETRYABLE,
            message=message,
        )

    def to_wire(self) -> dict[str, Any]:
        """Serialize to the camelCase dict an MCP client receives."""
        return self.model_dump(by_alias=True, exclude_none=True)
