"""tests/tools/test_check_docs_structure.py
Tests for tools/check_docs_structure.py.

No test file existed for this tool before plans/20260903-125706_plan.md
(docmeta03) added the `--schema` flag and `check_schema_compliance()`; this
file focuses on that new, opt-in behavior plus a light regression check that
the tool's pre-existing default behavior (no --schema) is unaffected.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools._front_matter_schema import load_front_matter_schema
from tools.check_docs_structure import check_schema_compliance, validate_file


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


_COMPLIANT_DOC = (
    "---\n"
    'title: "Example"\n'
    "area: agent\n"
    "tags:\n"
    "  - agent\n"
    "related:\n"
    "---\n\n"
    "# Example\n\n"
    "Body.\n\n"
    "## Related Documents\n\n"
    "## Keywords\n"
)


class TestSchemaComplianceRequiredFields:
    def test_compliant_document_passes(self, tmp_path: Path) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert issues == []

    def test_missing_required_field_is_flagged(self, tmp_path: Path) -> None:
        content = '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n---\n\nBody.\n'
        doc = _write(tmp_path / "example.md", content)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert any("related" in i for i in issues)

    def test_missing_front_matter_entirely_is_not_double_reported(
        self, tmp_path: Path
    ) -> None:
        """check_front_matter() already reports this case; schema compliance
        must return early rather than duplicating the finding."""
        doc = _write(tmp_path / "example.md", "# No front matter\n\nBody.\n")
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert issues == []


class TestSchemaComplianceEnums:
    def test_area_outside_enum_is_flagged(self, tmp_path: Path) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps(
                {
                    "required": ["title", "area", "tags", "related"],
                    "properties": {"area": {"enum": ["rag", "mcp"]}},
                }
            )
        )
        schema = load_front_matter_schema(schema_path)
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert len(issues) == 1
        assert "agent" in issues[0]

    def test_area_inside_enum_passes(self, tmp_path: Path) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps(
                {
                    "required": ["title", "area", "tags", "related"],
                    "properties": {"area": {"enum": ["agent", "rag"]}},
                }
            )
        )
        schema = load_front_matter_schema(schema_path)
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert issues == []

    def test_status_outside_enum_is_flagged(self, tmp_path: Path) -> None:
        content = _COMPLIANT_DOC.replace("area: agent", "area: agent\nstatus: obsolete")
        doc = _write(tmp_path / "example.md", content)
        schema_path = tmp_path / "doc_front_matter.json"
        schema_path.write_text(
            json.dumps(
                {
                    "required": ["title", "area", "tags", "related"],
                    "properties": {"status": {"enum": ["draft", "stable"]}},
                }
            )
        )
        schema = load_front_matter_schema(schema_path)
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert len(issues) == 1
        assert "obsolete" in issues[0]


class TestValidateFileSchemaOptIn:
    """validate_file()'s `schema` parameter defaults to None — passing it
    changes nothing about the tool's pre-existing checks (size, H1 count,
    front matter presence, tail sections, links)."""

    def test_no_schema_argument_preserves_existing_behavior(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        assert validate_file(doc, expected_area=None) == []

    def test_schema_argument_adds_findings_without_schema_file(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema = load_front_matter_schema(tmp_path / "absent.json")
        # Built-in default schema matches the tool's own existing required
        # fields exactly, so passing it adds no new findings for a compliant doc.
        assert validate_file(doc, expected_area=None, schema=schema) == []
