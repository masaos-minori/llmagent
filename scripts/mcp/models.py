#!/usr/bin/env python3
"""mcp_models.py
Shared Pydantic models for the /v1/call_tool unified endpoint.
Used by FileopMCPServer.py, WebSearchMCPServer.py, and GithubMCPServer.py.
"""

from pydantic import BaseModel, Field, field_validator

from mcp.tool_validators import validate_tool_args


class CallToolRequest(BaseModel):
    """Request body for POST /v1/call_tool."""

    name: str = Field(..., description="Tool name")
    args: dict[str, object] = Field(default_factory=dict, description="Tool arguments")

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

        Must be called explicitly before dispatching the tool call.
        Pydantic does not call this automatically.
        Raises ValueError when args violate tool constraints.
        """
        validate_tool_args(self.name, self.args)


class CallToolResponse(BaseModel):
    """Response body for POST /v1/call_tool."""

    result: str = Field(..., description="Formatted result text")
    is_error: bool = Field(..., description="True when the tool call failed")
