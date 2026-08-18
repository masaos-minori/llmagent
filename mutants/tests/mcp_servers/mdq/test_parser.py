"""tests/mcp_servers/mdq/test_parser.py

Characterization tests for `scripts/mcp_servers/mdq/parser.py`, added ahead of a
structural refactor (extraction of the frontmatter-parsing block into a helper
function). Existing coverage in `tests/mcp_servers/mdq/test_mdq_service.py`
(`TestParseMarkdown`) exercises the module at 98% line coverage; this file adds
the one previously-uncovered branch (invalid YAML syntax in frontmatter raising
`yaml.YAMLError`, not just a well-formed-but-wrong-shape `tags` value) so the
extracted helper is fully behavior-locked before transformation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.mdq_models import ParseMarkdownRequest
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.parser import parse_markdown


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
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
        sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        title_section = next(s for s in sections if s["heading"] == "Title")
        assert title_section["content"] == "Body."

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
        sections, tags = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        assert tags == []
        root_section = next(s for s in sections if s["heading"] == "<root>")
        assert "---" in root_section["content"]
        assert "title: Test" in root_section["content"]
        title_section = next(s for s in sections if s["heading"] == "Title")
        assert title_section["content"] == "Body."
