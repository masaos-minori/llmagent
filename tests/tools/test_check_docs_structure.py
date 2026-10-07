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

import pytest
import yaml

from tools._front_matter_schema import load_front_matter_schema
from tools.check_docs_structure import (
    MAX_SIZE,
    SIZE_EXCEPTIONS,
    _build_basename_index,
    _validate_related_format,
    check_adr_related_coverage,
    check_links,
    check_related_links,
    check_schema_compliance,
    check_size,
    check_status_value,
    check_tail_sections,
    check_unique_adr_ids,
    validate_file,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
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

    def test_category_only_fixture_is_flagged_for_missing_area(
        self, tmp_path: Path
    ) -> None:
        """REQ-004's literal named fixture: a document using `category:`
        instead of `area:` is flagged for the missing required `area` field.
        `check_schema_compliance()` has no `additionalProperties` check, so
        this produces the same finding as any other `area:`-less fixture —
        this test exists to match REQ-004's exact wording, not to exercise a
        new code path."""
        content = (
            '---\ntitle: "Example"\ncategory: agent\ntags:\n  - agent\n'
            "related:\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        schema = load_front_matter_schema(tmp_path / "no_schema_here.json")
        issues = check_schema_compliance(doc, doc.read_text(), schema)
        assert any("area" in i for i in issues)

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


class TestCheckStatusValue:
    def test_missing_status_field_passes(self, tmp_path: Path) -> None:
        """REQ-002: Documents without a 'status' field pass validation (defaults to stable)."""
        content = _COMPLIANT_DOC.replace("area: agent\n", "")
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_stable_passes(self, tmp_path: Path) -> None:
        """REQ-003: Documents with 'status: stable' pass validation."""
        content = (
            "---\n"
            'title: "Example"\n'
            "area: agent\n"
            "tags:\n"
            "  - agent\n"
            "related:\n"
            "status: stable\n"
            "---\n\n"
            "# Example\n\n"
            "Body.\n\n"
            "## Keywords\n"
        )
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_draft_passes(self, tmp_path: Path) -> None:
        """REQ-003: Documents with 'status: draft' pass validation."""
        content = (
            "---\n"
            'title: "Example"\n'
            "area: agent\n"
            "tags:\n"
            "  - agent\n"
            "related:\n"
            "status: draft\n"
            "---\n\n"
            "# Example\n\n"
            "Body.\n\n"
            "## Keywords\n"
        )
        doc = _write(tmp_path / "example.md", content)
        data = yaml.safe_load(content.split("---")[1]) or {}
        assert check_status_value(doc, data) == []

    def test_status_invalid_is_flagged(self, tmp_path: Path) -> None:
        """REQ-004: Documents with invalid 'status' values report an error."""
        for invalid_value in ("deprecated", "superseded", "stabel"):
            content = (
                "---\n"
                'title: "Example"\n'
                "area: agent\n"
                "tags:\n"
                "  - agent\n"
                "related:\n"
                f"status: {invalid_value}\n"
                "---\n\n"
                "# Example\n\n"
                "Body.\n\n"
                "## Keywords\n"
            )
            doc = _write(tmp_path / "example.md", content)
            data = yaml.safe_load(content.split("---")[1]) or {}
            issues = check_status_value(doc, data)
            assert len(issues) == 1
            assert invalid_value in issues[0]
            assert "not one of ['stable', 'draft']" in issues[0]


class TestCheckSize:
    """Regression for MAX_SIZE (raised 2026-09-03, see the constant's own
    comment): a governance doc consolidation needed more headroom than the
    old 16384-byte limit allowed."""

    def test_file_at_limit_passes(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        assert check_size(doc, MAX_SIZE) == []

    def test_file_over_limit_is_flagged(self, tmp_path: Path) -> None:
        doc = tmp_path / "example.md"
        issues = check_size(doc, MAX_SIZE + 1)
        assert len(issues) == 1
        assert str(MAX_SIZE) in issues[0]

    def test_file_between_old_and_new_limit_passes(self, tmp_path: Path) -> None:
        """19183 bytes is what docs/00_governance/governance_01_documentation-policy.md
        grew to under plans/20260902-191512_plan.md's REQ-001 change — this
        must pass under the raised limit even though it exceeded the old one."""
        doc = tmp_path / "example.md"
        assert check_size(doc, 19183) == []


class TestCheckSizeExceptions:
    """A per-file ceiling above MAX_SIZE applies only to the listed basename and
    equals the accepted size, so further growth is still caught."""

    def test_excepted_file_passes_up_to_its_ceiling(self, tmp_path: Path) -> None:
        name, ceiling = next(iter(SIZE_EXCEPTIONS.items()))
        assert ceiling > MAX_SIZE
        assert check_size(tmp_path / name, ceiling) == []

    def test_excepted_file_is_flagged_above_its_ceiling(self, tmp_path: Path) -> None:
        name, ceiling = next(iter(SIZE_EXCEPTIONS.items()))
        issues = check_size(tmp_path / name, ceiling + 1)
        assert len(issues) == 1
        assert f"exceeds {ceiling} byte limit" in issues[0]

    def test_other_files_keep_the_global_limit(self, tmp_path: Path) -> None:
        _, ceiling = next(iter(SIZE_EXCEPTIONS.items()))
        issues = check_size(tmp_path / "other.md", ceiling)
        assert issues == [
            f"other.md: size {ceiling} bytes exceeds {MAX_SIZE} byte limit"
        ]


class TestValidateFileSchemaOptIn:
    """validate_file()'s `schema` parameter defaults to None — passing it
    changes nothing about the tool's pre-existing checks (size, H1 count,
    front matter presence, tail sections, links)."""

    def test_no_schema_argument_preserves_existing_behavior(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        assert validate_file(doc, expected_area=None, basename_index={}) == []

    def test_schema_argument_adds_findings_without_schema_file(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema = load_front_matter_schema(tmp_path / "absent.json")
        # Built-in default schema matches the tool's own existing required
        # fields exactly, so passing it adds no new findings for a compliant doc.
        assert (
            validate_file(doc, expected_area=None, schema=schema, basename_index={})
            == []
        )


class TestCheckUniqueAdrIds:
    def test_no_duplicate_adr_ids_passes(self, tmp_path: Path) -> None:
        adr1 = _write(tmp_path / "ADR-001-example.md", "# ADR-001\n")
        adr2 = _write(tmp_path / "ADR-002-example.md", "# ADR-002\n")
        issues = check_unique_adr_ids([adr1, adr2])
        assert issues == []

    def test_duplicate_adr_id_is_flagged(self, tmp_path: Path) -> None:
        adr1 = _write(tmp_path / "ADR-001-first.md", "# ADR-001\n")
        adr2 = _write(tmp_path / "ADR-001-second.md", "# ADR-001\n")
        issues = check_unique_adr_ids([adr1, adr2])
        assert len(issues) == 1
        assert "ADR-001" in issues[0]
        assert "first.md" in issues[0]
        assert "second.md" in issues[0]

    def test_non_adr_files_are_ignored(self, tmp_path: Path) -> None:
        other1 = _write(tmp_path / "other1.md", "# Other\n")
        other2 = _write(tmp_path / "other2.md", "# Other\n")
        issues = check_unique_adr_ids([other1, other2])
        assert issues == []

    def test_mixed_adr_and_non_adr_files(self, tmp_path: Path) -> None:
        adr = _write(tmp_path / "ADR-001-example.md", "# ADR-001\n")
        other = _write(tmp_path / "other.md", "# Other\n")
        issues = check_unique_adr_ids([adr, other])
        assert issues == []


class TestBasenameIndexResolution:
    def test_cross_directory_bare_filename_resolves(self, tmp_path: Path) -> None:
        _write(tmp_path / "sub" / "target.md", "# Target\n")
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        assert check_related_links(doc, doc.read_text(), index) == []

    def test_missing_basename_is_still_flagged(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - does-not-exist.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index)
        assert any("does-not-exist.md" in i for i in issues)

    def test_directory_qualified_reference_rejected(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - sub/target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        issues = check_related_links(doc, doc.read_text(), {})
        assert any("must be a plain basename" in i for i in issues)

    def test_body_link_cross_directory_resolves(self, tmp_path: Path) -> None:
        _write(tmp_path / "sub" / "target.md", "# Target\n")
        doc = _write(tmp_path / "example.md", "# Example\n\nSee [target](target.md).\n")
        index = _build_basename_index(tmp_path)
        assert check_links(doc, doc.read_text(), index) == []

    def test_body_link_missing_target_is_flagged(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [target](does-not-exist.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index)
        assert any("does-not-exist.md" in i for i in issues)


class TestDuplicateBasenameDetection:
    def test_duplicate_basename_raises(self, tmp_path: Path) -> None:
        _write(tmp_path / "a" / "dup.md", "# A\n")
        _write(tmp_path / "b" / "dup.md", "# B\n")
        with pytest.raises(ValueError, match="dup.md"):
            _build_basename_index(tmp_path)


class TestDefaultGlobIsRecursive:
    def test_recursive_glob_finds_subdirectory_file(self, tmp_path: Path) -> None:
        _write(tmp_path / "top.md", "# Top\n")
        _write(tmp_path / "sub" / "nested.md", "# Nested\n")
        found = set(tmp_path.glob("**/*.md"))
        assert len(found) == 2


class TestSelfReferenceCheck:
    """GV-005: Self-reference prohibition check."""

    def test_self_reference_in_body_link_is_flagged(self, tmp_path: Path) -> None:
        """REQ-008: A document linking to itself in body text is flagged."""
        doc = _write(
            tmp_path / "example.md", "# Example\n\nSee [example](example.md).\n"
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index)
        assert any("self-reference detected" in i for i in issues)

    def test_self_reference_in_related_field_is_flagged(self, tmp_path: Path) -> None:
        """REQ-008: A document referencing itself in 'related' front-matter is flagged."""
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - example.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index)
        assert any("self-reference detected" in i for i in issues)

    def test_cross_directory_self_reference_with_path_is_flagged(
        self, tmp_path: Path
    ) -> None:
        """REQ-004: Self-reference with relative path across directories is detected."""
        _write(tmp_path / "sub" / "example.md", "# Example\n")
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - ./example.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "sub" / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index)
        assert any("self-reference detected" in i for i in issues)

    def test_normal_cross_reference_passes(self, tmp_path: Path) -> None:
        """REQ-009: Normal cross-references do not trigger false positives."""
        _write(tmp_path / "other.md", "# Other\n")
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - other.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index)
        assert not any("self-reference" in i for i in issues)

    def test_bare_basename_self_reference_guard_works(self, tmp_path: Path) -> None:
        """The target != path.name guard skips resolution when the string equals the filename."""
        doc = _write(tmp_path / "same.md", "# Same\n\nSee [same](same.md).\n")
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index)
        assert any("self-reference detected" in i for i in issues)


class TestValidateFileStatusIntegration:
    """REQ-008: Integration test confirming the check runs in `validate_file()` flow."""

    def test_validate_file_reports_invalid_status_without_schema_arg(
        self, tmp_path: Path
    ) -> None:
        """Invalid status value is reported even when --schema is not passed explicitly,
        because check_status_value() is called unconditionally in validate_file()."""
        content = (
            "---\n"
            'title: "Example"\n'
            "area: agent\n"
            "tags:\n"
            "  - agent\n"
            "related:\n"
            "status: obsolete\n"
            "---\n\n"
            "# Example\n\n"
            "Body.\n\n"
            "## Keywords\n"
        )
        doc = _write(tmp_path / "example.md", content)
        # No schema argument — check_status_value() should still catch it
        issues = validate_file(doc, expected_area=None, basename_index={})
        assert any("obsolete" in i for i in issues)

    def test_validate_file_accepts_valid_status(self, tmp_path: Path) -> None:
        """Valid status values are accepted in validate_file() flow."""
        for status_val in ("stable", "draft"):
            content = (
                "---\n"
                'title: "Example"\n'
                f"area: agent\n"
                "tags:\n"
                "  - agent\n"
                "related:\n"
                f"status: {status_val}\n"
                "---\n\n"
                "# Example\n\n"
                "Body.\n\n"
                "## Keywords\n"
            )
            doc = _write(tmp_path / "example.md", content)
            issues = validate_file(doc, expected_area=None, basename_index={})
            assert not any("status" in i for i in issues), (
                f"Unexpected status issue for '{status_val}': {issues}"
            )


class TestDuplicateRelatedLinks:
    """REQ-001: Duplicate entries in the 'related' front-matter field are detected."""

    def test_duplicate_related_link_is_flagged(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - target.md\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("duplicate related link" in i for i in issues)

    def test_unique_related_links_pass(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - target.md\n  - other.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index, check_duplicates=True)
        assert not any("duplicate" in i for i in issues)

    def test_duplicate_source_link_is_flagged(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "source:\n  - source.md\n  - source.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("duplicate related link" in i for i in issues)

    def test_mixed_path_formats_detected_as_duplicate(self, tmp_path: Path) -> None:
        _write(tmp_path / "sub" / "target.md", "# Target\n")
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - sub/target.md\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("duplicate related link" in i for i in issues)

    def test_no_false_positive_for_different_files_same_basename(
        self, tmp_path: Path
    ) -> None:
        """Two different files with the same basename should NOT be flagged as duplicates
        since they resolve to different resolved paths."""
        _write(tmp_path / "a" / "dup.md", "# A\n")
        _write(tmp_path / "b" / "dup.md", "# B\n")
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - a/dup.md\n  - b/dup.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        issues = check_related_links(doc, doc.read_text(), {}, check_duplicates=True)
        assert not any("duplicate" in i for i in issues)

    def test_duplicate_count_shown_in_message(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - target.md\n  - target.md\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("appears 3 times" in i for i in issues)

    def test_duplicate_detection_disabled_by_default(self, tmp_path: Path) -> None:
        content = (
            '---\ntitle: "Example"\narea: agent\ntags:\n  - agent\n'
            "related:\n  - target.md\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(
            doc, doc.read_text(), index, check_duplicates=False
        )
        assert not any("duplicate" in i for i in issues)


class TestDuplicateBodyLinks:
    """REQ-003: Duplicate Markdown links within body text are detected."""

    def test_duplicate_body_link_is_flagged(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](target.md) and [another](target.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("duplicate link" in i for i in issues)

    def test_unique_body_links_pass(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](target.md) and [other](other.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=True)
        assert not any("duplicate" in i for i in issues)

    def test_duplicate_count_shown_in_message(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](target.md) and [another](target.md) and [third](target.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("appears 3 times" in i for i in issues)

    def test_duplicate_detection_disabled_by_default(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](target.md) and [another](target.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=False)
        assert not any("duplicate" in i for i in issues)

    def test_http_links_not_checked_for_duplicates(self, tmp_path: Path) -> None:
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](http://example.com) and [another](http://example.com).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=True)
        assert not any("duplicate" in i for i in issues)

    def test_cross_directory_duplicate_detected(self, tmp_path: Path) -> None:
        _write(tmp_path / "sub" / "target.md", "# Target\n")
        doc = _write(
            tmp_path / "example.md",
            "# Example\n\nSee [link](sub/target.md) and [another](target.md).\n",
        )
        index = _build_basename_index(tmp_path)
        issues = check_links(doc, doc.read_text(), index, check_duplicates=True)
        assert any("duplicate link" in i for i in issues)


# ---------------------------------------------------------------------------
# Related section rules: ADR requires the block; non-ADR must use front matter
# ---------------------------------------------------------------------------

_ADR_BODY = (
    "# ADR\n\n## Related Documents\n\n### Specifications\n\n"
    "- `a.md`\n- [B](b.md#x)\n- `missing_target.md`\n\n## Keywords\n"
)


def _adr_content(related: str) -> str:
    return f"---\ntitle: T\narea: governance\ntags:\n  - x\nrelated:{related}\n---\n\n{_ADR_BODY}"


class TestRelatedSectionRules:
    def test_adr_without_related_documents_is_reported(self, tmp_path: Path) -> None:
        adr = tmp_path / "10_adr" / "ADR-001-x.md"
        issues = check_tail_sections(adr, "# ADR\n\n## Keywords\n")
        assert issues == ["ADR-001-x.md: missing '## Related Documents' section"]

    def test_non_adr_without_related_documents_passes(self, tmp_path: Path) -> None:
        assert check_tail_sections(tmp_path / "doc.md", "# T\n\n## Keywords\n") == []

    @pytest.mark.parametrize(
        "heading", ["Related Documents", "Related Docs", "Related Chapters"]
    )
    def test_non_adr_related_section_is_reported(
        self, tmp_path: Path, heading: str
    ) -> None:
        content = f"# T\n\n## {heading}\n\n- `a.md`\n\n## Keywords\n"
        issues = check_tail_sections(tmp_path / "doc.md", content)
        assert len(issues) == 1
        assert f"## {heading}" in issues[0]
        assert "front matter 'related:'" in issues[0]

    def test_related_heading_inside_code_fence_is_ignored(self, tmp_path: Path) -> None:
        content = "# T\n\n```\n## Related Documents\n```\n\n## Keywords\n"
        assert check_tail_sections(tmp_path / "doc.md", content) == []

    def test_keywords_section_is_still_required(self, tmp_path: Path) -> None:
        issues = check_tail_sections(tmp_path / "doc.md", "# T\n")
        assert issues == ["doc.md: missing '## Keywords' section"]


class TestAdrRelatedCoverage:
    def _index(self, tmp_path: Path) -> dict[str, Path]:
        return {n: tmp_path / n for n in ("a.md", "b.md", "ADR-001-x.md")}

    def test_missing_body_reference_is_reported(self, tmp_path: Path) -> None:
        adr = tmp_path / "10_adr" / "ADR-001-x.md"
        issues = check_adr_related_coverage(
            adr, _adr_content("\n  - a.md"), self._index(tmp_path)
        )
        assert issues == [
            "ADR-001-x.md: front matter 'related:' lacks body-referenced "
            "document 'b.md'"
        ]

    def test_covered_adr_passes_and_unresolved_target_is_not_reported(
        self, tmp_path: Path
    ) -> None:
        adr = tmp_path / "10_adr" / "ADR-001-x.md"
        content = _adr_content("\n  - a.md\n  - ../b.md")
        assert check_adr_related_coverage(adr, content, self._index(tmp_path)) == []

    def test_non_adr_is_not_checked(self, tmp_path: Path) -> None:
        doc = tmp_path / "doc.md"
        assert (
            check_adr_related_coverage(doc, _adr_content(" []"), self._index(tmp_path))
            == []
        )

    def test_adr_without_front_matter_or_with_bad_yaml_is_skipped(
        self, tmp_path: Path
    ) -> None:
        adr = tmp_path / "10_adr" / "ADR-001-x.md"
        index = self._index(tmp_path)
        assert check_adr_related_coverage(adr, "# no front matter\n", index) == []
        assert check_adr_related_coverage(adr, "---\ntitle: T\n", index) == []
        assert check_adr_related_coverage(adr, "---\n: [bad\n---\n", index) == []

    def test_validate_file_reports_adr_coverage_gap(self, tmp_path: Path) -> None:
        adr = _write(tmp_path / "10_adr" / "ADR-001-x.md", _adr_content("\n  - a.md"))
        _write(tmp_path / "a.md", _COMPLIANT_DOC)
        _write(tmp_path / "b.md", _COMPLIANT_DOC)
        index = _build_basename_index(tmp_path)
        issues = validate_file(adr, None, None, basename_index=index)
        assert any("lacks body-referenced document 'b.md'" in i for i in issues)


# ---------------------------------------------------------------------------
# Any-level body Related detection + related: format validation (rel001)
# ---------------------------------------------------------------------------


class TestCheckTailSectionsAnyLevel:
    """Any-level body Related Documents detection in non-ADR docs."""

    def test_body_related_at_h2_level_reported(self) -> None:
        content = "## Related Documents\n\n- `foo.md`\n\n## Keywords\n\nx\n"
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 1
        assert (
            "non-ADR document must not carry a body '## Related Documents' section"
            in issues[0]
        )

    def test_body_related_at_h3_level_reported(self) -> None:
        content = "### Related Documents\n\n- `foo.md`\n\n## Keywords\n\nx\n"
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 1
        assert (
            "non-ADR document must not carry a body '### Related Documents' section"
            in issues[0]
        )

    def test_heading_inside_fenced_code_ignored(self) -> None:
        content = "```\n## Related Documents\n```\n\n## Keywords\n\nx\n"
        issues = check_tail_sections(Path("test.md"), content)
        assert len(issues) == 0

    def test_adr_related_documents_required(self) -> None:
        content = "# Some ADR\n\n## Keywords\n\nx\n"
        issues = check_tail_sections(Path("docs/10_adr/ADR-001-test.md"), content)
        assert len(issues) == 1
        assert "missing '## Related Documents' section" in issues[0]


class TestValidateRelatedFormat:
    """related: entries must be plain .md basenames (no path/anchor)."""

    def test_empty_list_accepted(self) -> None:
        assert _validate_related_format([]) == []

    def test_valid_basename_accepted(self) -> None:
        assert _validate_related_format(["foo.md"]) == []

    def test_invalid_extension_rejected(self) -> None:
        issues = _validate_related_format(["foo.txt"])
        assert len(issues) == 1
        assert "must end in '.md'" in issues[0]

    def test_path_in_entry_rejected(self) -> None:
        issues = _validate_related_format(["subdir/foo.md"])
        assert len(issues) == 1
        assert "must be a plain basename" in issues[0]

    def test_anchor_in_entry_rejected(self) -> None:
        issues = _validate_related_format(["foo.md#section"])
        assert any("must be a plain basename" in i for i in issues)
