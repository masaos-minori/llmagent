"""tests/mcp_servers/test_request_contract.py

Unit tests for the shared strict request contract (Plan T-01).

Covers `build_input_schema()` determinism, preservation of every validation
keyword pydantic declares, retention of `$defs`/`$ref`, stripping of generated
`title` keys only, and `StrictRequestModel` unknown-field rejection.
"""

from __future__ import annotations

from typing import Any, Literal

import pytest
from mcp_servers.request_contract import StrictRequestModel, build_input_schema
from pydantic import BaseModel, Field, ValidationError


class _Nested(BaseModel):
    path: str = Field(..., min_length=1, description="File path")
    content: str = Field(..., max_length=1048576)


class _SampleRequest(StrictRequestModel):
    owner: str = Field(..., min_length=1, max_length=100, description="Owner name")
    title: str = Field(..., min_length=1, max_length=256)
    state: Literal["open", "closed", "all"] = Field(default="open")
    per_page: int = Field(default=10, ge=1, le=100)
    ref: str = Field(default="", pattern="^[A-Za-z0-9._/-]+$")
    labels: list[str] = Field(default_factory=list, max_length=100)
    files: list[_Nested] = Field(default_factory=list, min_length=1, max_length=100)


def _schema_nodes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect every schema node (root, `$defs` entries, sub-schemas) of `schema`."""
    nodes: list[dict[str, Any]] = [schema]
    for key, value in schema.items():
        if key in {"properties", "$defs", "patternProperties"} and isinstance(
            value, dict
        ):
            for sub_schema in value.values():
                if isinstance(sub_schema, dict):
                    nodes.extend(_schema_nodes(sub_schema))
        elif isinstance(value, dict):
            nodes.extend(_schema_nodes(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    nodes.extend(_schema_nodes(item))
    return nodes


class TestStrictRequestModel:
    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError):
            _SampleRequest.model_validate({"owner": "o", "repo": "r", "unexpected": 1})

    def test_accepts_declared_fields(self) -> None:
        request = _SampleRequest.model_validate({"owner": "octocat", "title": "Fix"})
        assert request.owner == "octocat"
        assert request.per_page == 10


class TestBuildInputSchema:
    def test_strips_generated_title_keys(self) -> None:
        schema = build_input_schema(_SampleRequest)
        for node in _schema_nodes(schema):
            assert "title" not in node

    def test_keeps_a_field_named_title(self) -> None:
        schema = build_input_schema(_SampleRequest)
        assert schema["properties"]["title"] == {
            "type": "string",
            "minLength": 1,
            "maxLength": 256,
        }
        assert "title" in schema["required"]

    def test_preserves_validation_keywords(self) -> None:
        properties = build_input_schema(_SampleRequest)["properties"]
        assert properties["owner"]["minLength"] == 1
        assert properties["owner"]["maxLength"] == 100
        assert properties["owner"]["description"] == "Owner name"
        assert properties["title"]["minLength"] == 1
        assert properties["title"]["maxLength"] == 256
        assert properties["state"]["enum"] == ["open", "closed", "all"]
        assert properties["state"]["default"] == "open"
        assert properties["per_page"]["minimum"] == 1
        assert properties["per_page"]["maximum"] == 100
        assert properties["per_page"]["default"] == 10
        assert properties["ref"]["pattern"] == "^[A-Za-z0-9._/-]+$"
        assert properties["labels"]["maxItems"] == 100
        assert properties["files"]["minItems"] == 1
        assert properties["files"]["maxItems"] == 100

    def test_preserves_defs_and_ref(self) -> None:
        schema = build_input_schema(_SampleRequest)
        assert schema["$defs"]["_Nested"]["properties"]["path"]["minLength"] == 1
        assert schema["properties"]["files"]["items"] == {"$ref": "#/$defs/_Nested"}

    def test_preserves_required_and_additional_properties(self) -> None:
        schema = build_input_schema(_SampleRequest)
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["owner", "title"]

    def test_is_deterministic_across_repeated_calls(self) -> None:
        first = build_input_schema(_SampleRequest)
        second = build_input_schema(_SampleRequest)
        assert first == second
        assert list(first) == list(second)
        assert list(first["properties"]) == list(second["properties"])

    def test_does_not_reorder_or_rename_keys(self) -> None:
        raw = _SampleRequest.model_json_schema()
        generated = build_input_schema(_SampleRequest)
        assert [key for key in raw if key != "title"] == list(generated)
        for name, sub_schema in raw["properties"].items():
            assert [key for key in sub_schema if key != "title"] == list(
                generated["properties"][name]
            )

    def test_does_not_mutate_the_model_schema(self) -> None:
        build_input_schema(_SampleRequest)
        assert "title" in _SampleRequest.model_json_schema()

    def test_accepts_a_model_without_the_strict_base(self) -> None:
        schema = build_input_schema(_Nested)
        assert schema["properties"]["path"]["minLength"] == 1
        assert "additionalProperties" not in schema
