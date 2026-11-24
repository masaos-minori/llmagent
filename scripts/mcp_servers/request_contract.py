#!/usr/bin/env python3
"""scripts/mcp_servers/request_contract.py — Shared strict request contract for MCP server domains.

`StrictRequestModel` is the base a tool request model inherits so arguments
outside the declared fields are rejected instead of silently dropped.
`build_input_schema()` publishes that same model as the tool `inputSchema`, so
the contract a client discovers at `/v1/tools` is the contract the server
enforces at call time.

Dependency direction: mcp_servers.request_contract → (external: pydantic only)

Usage:
    from mcp_servers.request_contract import StrictRequestModel, build_input_schema

    class ListRequest(StrictRequestModel):
        owner: str = Field(..., min_length=1)

    tool["inputSchema"] = build_input_schema(ListRequest)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = ["StrictRequestModel", "build_input_schema"]

# Maps whose keys are field or definition names, not schema nodes: their keys
# must survive the presentation-field pass (a model field named `title` is one).
_SUBSCHEMA_MAP_KEYS = frozenset({"properties", "$defs", "patternProperties"})


class StrictRequestModel(BaseModel):
    """Base for tool request models: unknown arguments are rejected.

    Same posture as the `extra="forbid"` wire models in
    `scripts/mcp_servers/models.py`.
    """

    model_config = ConfigDict(extra="forbid")


def build_input_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return the JSON Schema of `model` as a tool `inputSchema`.

    Every validation keyword the model declares passes through unchanged. Only
    generated `title` keys, which carry no validation meaning, are removed.
    """
    schema: dict[str, Any] = model.model_json_schema()
    _strip_presentation_fields(schema)
    return schema


def _strip_presentation_fields(node: dict[str, Any]) -> None:
    """Remove generated `title` keys from `node` and its sub-schemas in place."""
    node.pop("title", None)
    for key, value in node.items():
        if key in _SUBSCHEMA_MAP_KEYS and isinstance(value, dict):
            for sub_schema in value.values():
                if isinstance(sub_schema, dict):
                    _strip_presentation_fields(sub_schema)
        elif isinstance(value, dict):
            _strip_presentation_fields(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _strip_presentation_fields(item)
