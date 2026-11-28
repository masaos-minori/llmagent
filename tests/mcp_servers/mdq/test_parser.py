"""tests/mcp_servers/mdq/test_parser.py

Characterization tests for `scripts/mcp_servers/mdq/parser.py`, added ahead of a
structural refactor (extraction of the frontmatter-parsing block into a helper
function). Existing coverage in `tests/mcp_servers/mdq/test_mdq_service.py`
(`TestParseMarkdown`) exercises the module at 98% line coverage; this file adds
the one previously-uncovered branch (invalid YAML syntax in frontmatter raising
`yaml.YAMLError`, not just a well-formed-but-wrong-shape `tags` value) so the
extracted helper is fully behavior-locked before transformation. The
`TestFrontmatterInvalidYamlSyntax` cases also pin the structured `invalid_frontmatter`
warning record (REQ-007) and the decoded-character count (REQ-004).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.mdq_models import ParseMarkdownRequest
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.parser import parse_markdown

from tests.mcp_servers.mdq._startup import make_startup


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        import os

        os.close(fd)


class TestFrontmatterInvalidYamlSyntax:
    def test_invalid_yaml_syntax_falls_back_to_empty_tags(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Frontmatter whose body is not even syntactically valid YAML (as opposed
        to well-formed YAML with the wrong shape) raises `yaml.YAMLError` inside
        `yaml.safe_load`. That error must be swallowed and `tags` must fall back
        to an empty list, without interrupting parsing of the rest of the file.
        """
        f = tmp_path / "invalid_yaml.md"
        f.write_text(
            "---\ntags: [unterminated\n  nested: - bad\n---\n\n# Title\n\nBody.",
            encoding="utf-8",
        )
        sections, tags, _warning = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        title_section = next(s for s in sections if s["heading"] == "Title")
        assert title_section["content"] == "Body."

    def test_invalid_yaml_syntax_records_structured_warning(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """The swallowed `yaml.YAMLError` must be observable as a structured warning
        record (REQ-007): a stable code and a count. The record carries codes and
        counts only, so no absolute path appears in it.
        """
        f = tmp_path / "invalid_yaml_warning.md"
        f.write_text(
            "---\ntags: [unterminated\n  nested: - bad\n---\n\n# Title\n\nBody.",
            encoding="utf-8",
        )
        _sections, tags, warning = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        assert warning["warning_codes"] == ["invalid_frontmatter"]
        assert warning["warning_count"] == 1
        assert str(f) not in str(warning)

    def test_valid_frontmatter_reports_an_empty_warning_record(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A file whose frontmatter parses yields no warning codes and no count."""
        f = tmp_path / "valid.md"
        f.write_text("---\ntags: [a]\n---\n\n# Title\n\nBody.", encoding="utf-8")
        _sections, tags, warning = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == ["a"]
        assert warning["warning_codes"] == []
        assert warning["warning_count"] == 0

    def test_char_count_counts_decoded_characters_not_bytes(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """The record reports the decoded-character count, which is a different number
        from the on-disk byte count the indexer's size gate measures (REQ-004).
        """
        text = "# Title\n\n日本語と emoji 🎉 の mixed content."
        f = tmp_path / "multibyte.md"
        f.write_text(text, encoding="utf-8")
        _sections, _tags, warning = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert warning["char_count"] == len(text)
        assert warning["char_count"] < len(text.encode("utf-8"))

    def test_unclosed_frontmatter_delimiter_treated_as_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """A leading '---' line with no matching closing '---' anywhere in the
        file is not frontmatter at all — it must fall through to being treated as
        ordinary (non-heading) content in the `<root>` section, not swallow the
        rest of the file looking for a delimiter that never appears.
        """
        f = tmp_path / "unclosed.md"
        f.write_text("---\ntitle: Test\n\n# Title\n\nBody.", encoding="utf-8")
        sections, tags, _warning = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        root_section = next(s for s in sections if s["heading"] == "<root>")
        assert "---" in root_section["content"]
        assert "title: Test" in root_section["content"]
        title_section = next(s for s in sections if s["heading"] == "Title")
        assert title_section["content"] == "Body."
