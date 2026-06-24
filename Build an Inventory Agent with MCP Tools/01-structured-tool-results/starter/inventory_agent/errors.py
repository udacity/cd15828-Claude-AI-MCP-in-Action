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


# TODO: Only transient failures are worth retrying. Build the set of retryable categories so
# is_retryable can be derived from the category, not set by hand at every call site.
_RETRYABLE: set[ErrorCategory] = set()


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
        # TODO: Build a success envelope. A success has no error and carries only the data
        # payload (no category, no retryability, no message).
        raise NotImplementedError

    @classmethod
    def fail(cls, category: ErrorCategory, message: str) -> ToolResult:
        # TODO: Build a failure envelope. Set is_error, record the category and message, and
        # derive is_retryable from the category (use _RETRYABLE) rather than passing it in.
        raise NotImplementedError

    def to_wire(self) -> dict[str, Any]:
        """Serialize to the camelCase dict an MCP client receives."""
        # TODO: Serialize using the camelCase aliases (isError/errorCategory/isRetryable) and
        # drop fields that are None so a success result carries no empty error fields.
        raise NotImplementedError
