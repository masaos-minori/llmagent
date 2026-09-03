"""tests/tools/test_front_matter_schema.py
Tests for tools/_front_matter_schema.py — the shared Front Matter schema
loader used by both tools/check_docs_structure.py and
tools/manage_frontmatter.py to avoid duplicating the required-field set and
`area`/`status` enums across tools.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools._front_matter_schema import (
    DEFAULT_REQUIRED_FIELDS,
    load_front_matter_schema,
)


class TestFallbackWhenSchemaAbsent:
    """Before plans/20260903-124425_plan.md (docmeta01) authors
    schemas/doc_front_matter.json, every tool must see exactly today's
    hardcoded default — never a behavior change from this module's mere
    existence."""

    def test_missing_file_returns_built_in_default(self, tmp_path: Path) -> None:
        schema = load_front_matter_schema(tmp_path / "does_not_exist.json")
        assert schema.required_fields == DEFAULT_REQUIRED_FIELDS
        assert schema.area_enum is None
        assert schema.status_enum is None
        assert schema.source == "built-in default"

    def test_malformed_json_falls_back_to_default(self, tmp_path: Path) -> None:
        bad = tmp_path / "doc_front_matter.json"
        bad.write_text("{not valid json")
        schema = load_front_matter_schema(bad)
        assert schema.required_fields == DEFAULT_REQUIRED_FIELDS
        assert schema.area_enum is None


class TestSchemaFileParsing:
    """Once a real draft-07 schema file exists, its required/enum values —
    not the built-in default — become the source of truth."""

    def test_required_fields_loaded_from_schema(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps({"required": ["title", "area", "tags", "related", "status"]})
        )
        schema = load_front_matter_schema(schema_path)
        assert schema.required_fields == (
            "title",
            "area",
            "tags",
            "related",
            "status",
        )
        assert schema.source == str(schema_path)

    def test_area_and_status_enums_loaded_from_schema(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps(
                {
                    "required": ["title", "area", "tags", "related"],
                    "properties": {
                        "area": {"enum": ["agent", "rag", "mcp"]},
                        "status": {"enum": ["draft", "stable"]},
                    },
                }
            )
        )
        schema = load_front_matter_schema(schema_path)
        assert schema.area_enum == ("agent", "rag", "mcp")
        assert schema.status_enum == ("draft", "stable")

    def test_missing_enum_stays_none(self, tmp_path: Path) -> None:
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps(
                {
                    "required": ["title", "area", "tags", "related"],
                    "properties": {"area": {"type": "string"}},
                }
            )
        )
        schema = load_front_matter_schema(schema_path)
        assert schema.area_enum is None
        assert schema.status_enum is None
