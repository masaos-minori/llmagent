#!/usr/bin/env python3
"""mcp_models.py
Shared Pydantic models for the /v1/call_tool unified endpoint.
Used by FileopMCPServer.py, WebSearchMCPServer.py, and GithubMCPServer.py.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CallToolRequest(BaseModel):
    """Request body for POST /v1/call_tool."""

    name: str = Field(..., description="Tool name")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        """Reject blank tool names early so dispatch logic can assume non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Tool name must not be blank.")
        return stripped

    def validate_args(self) -> None:
        """Run tool-specific argument validation if a validator is registered.

        Raises ValueError when args violate tool constraints.
        """
        from mcp.tool_validators import validate_tool_args  # noqa: PLC0415

        validate_tool_args(self.name, self.args)


class CallToolResponse(BaseModel):
    """Response body for POST /v1/call_tool."""

    result: str = Field(..., description="Formatted result text")
    is_error: bool = Field(..., description="True when the tool call failed")
