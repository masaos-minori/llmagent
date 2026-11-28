"""tests/mcp_servers/mdq/test_db_grep.py

Direct unit tests for scripts/mcp_servers/mdq/db_grep.py — `find_grep_match` and
`grep_docs`. These exercise the module directly against an in-memory sqlite3
connection, independent of MdqService, to lock behavior before refactoring
(characterization tests per prompts/04_refactor.md Step 4).
"""

from __future__ import annotations

import re
import sqlite3

import pytest
from mcp_servers.mdq.db_grep import find_grep_match, grep_docs


@pytest.fixture
def conn() -> sqlite3.Connection:
    """In-memory sqlite3 connection with a minimal `chunks` table."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE chunks (
            chunk_id TEXT,
            source_path TEXT,
            heading_path TEXT,
            heading TEXT,
            content TEXT,
            start_line INTEGER
        )
        """
    )
    return connection


def _insert_chunk(
    connection: sqlite3.Connection,
    chunk_id: str,
    source_path: str,
    heading_path: str,
    heading: str,
    content: str,
    start_line: int = 1,
) -> None:
    connection.execute(
        "INSERT INTO chunks (chunk_id, source_path, heading_path, heading, content, start_line) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (chunk_id, source_path, heading_path, heading, content, start_line),
    )
    connection.commit()


class TestFindGrepMatch:
    def test_returns_no_matches_when_no_match(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Title", "nothing relevant here")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("xyz_not_present")
        assert (
            find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
            == []
        )

    def test_returns_match_on_first_line(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "hello world")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("world")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        match = matches[0]
        assert match.chunk_id == "c1"
        assert match.source_path == "a.md"
        assert match.heading_path == ""
        assert match.match_text == "world"
        # start_line 1 + 1 + k 0: `world` sits on the first stored content line (UNK-03)
        assert match.line_number == 2

    def test_matches_within_heading_line(self, conn: sqlite3.Connection) -> None:
        """A pattern that only matches the synthesized heading line (row['heading'])
        is found on the section's own start_line, since full_text = f"{heading}\\n{content}"."""
        _insert_chunk(conn, "c1", "a.md", "Parent", "UniqueHeading", "content body")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("UniqueHeading")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        assert matches[0].line_number == 1
        assert matches[0].heading_path == "Parent"

    def test_match_text_truncated_to_max_chars(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "aaaaaaaaaa")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("a+")
        matches = find_grep_match(row, compiled, max_chars=3, ctx_before=0, ctx_after=0)
        assert len(matches) == 1
        assert matches[0].match_text == "aaa"

    def test_multiple_matches_in_one_chunk_are_returned(
        self, conn: sqlite3.Connection
    ) -> None:
        """A chunk contributes every pattern hit up to the collector's cap (REQ-006)."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "foo foo foo")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("foo")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert [m.match_text for m in matches] == ["foo", "foo", "foo"]
        assert [m.line_number for m in matches] == [2, 2, 2]

    def test_line_number_for_match_on_later_line(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(
            conn, "c1", "a.md", "", "Intro", "line one\nline two\ntarget line"
        )
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("target")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        # start_line 1 + 1 + k 2: `target line` is the third stored content line (UNK-03)
        assert matches[0].line_number == 4

    def test_line_number_from_stored_start_line(self, conn: sqlite3.Connection) -> None:
        """The reported line is `start_line + 1 + k`, so a chunk stored at file line 10
        reports file lines, not a chunk-relative offset (UNK-03)."""
        _insert_chunk(
            conn,
            "c1",
            "a.md",
            "",
            "Intro",
            "line one\nline two\ntarget line",
            start_line=10,
        )
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("target")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        assert matches[0].line_number == 13

    def test_heading_match_reports_the_stored_start_line(
        self, conn: sqlite3.Connection
    ) -> None:
        """The synthetic heading line stands at the section's own `start_line`."""
        _insert_chunk(
            conn, "c1", "a.md", "Parent", "UniqueHeading", "body", start_line=10
        )
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("UniqueHeading")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        assert matches[0].line_number == 10

    def test_context_before_and_after_are_returned(
        self, conn: sqlite3.Connection
    ) -> None:
        """The requested context is part of the match, not a discarded local (REQ-006)."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "a1\na2\nneedle here\nb1\nb2")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("needle")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=2, ctx_after=2
        )
        assert len(matches) == 1
        assert matches[0].context_before_lines == ["a1", "a2"]
        assert matches[0].context_after_lines == ["b1", "b2"]

    def test_explicit_zero_context_is_honored(self, conn: sqlite3.Connection) -> None:
        """Zero context means no context lines, returned as empty lists (REQ-006)."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "a1\nneedle here\nb1")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("needle")
        matches = find_grep_match(
            row, compiled, max_chars=200, ctx_before=0, ctx_after=0
        )
        assert len(matches) == 1
        assert matches[0].context_before_lines == []
        assert matches[0].context_after_lines == []

    def test_context_clipped_to_max_chars(self, conn: sqlite3.Connection) -> None:
        """max_chars bounds the match text plus the returned context lines, counted as
        their joined length; the match text is exact and lines stay whole (REQ-006)."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "x1\nx2\nneedle here\ny1\ny2")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("needle here")
        matches = find_grep_match(
            row, compiled, max_chars=20, ctx_before=2, ctx_after=2
        )
        assert len(matches) == 1
        match = matches[0]
        assert match.match_text == "needle here"
        assert match.context_before_lines == ["x1", "x2"]
        assert match.context_after_lines == ["y1"]
        rendered = "\n".join(
            match.context_before_lines + [match.match_text] + match.context_after_lines
        )
        assert len(rendered) <= 20

    def test_multiline_pattern_semantics(self, conn: sqlite3.Connection) -> None:
        """`re.compile` is called with no flags, so a line-crossing match needs an
        explicit `\\n`, `^` anchors only at the text start, and every match is reported
        at the line where it starts (UNK-05)."""
        _insert_chunk(
            conn, "c1", "a.md", "", "Intro", "line one\nline two\ntarget line"
        )
        row = conn.execute("SELECT * FROM chunks").fetchone()
        matches = find_grep_match(
            row,
            re.compile("two\ntarget"),
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert len(matches) == 1
        # The match starts on "line two", the second stored content line: 1 + 1 + 1
        assert matches[0].line_number == 3
        assert (
            find_grep_match(
                row,
                re.compile("^line one"),
                max_chars=200,
                ctx_before=0,
                ctx_after=0,
            )
            == []
        )


class TestGrepDocs:
    def test_no_matches_returns_placeholder_text_and_metadata(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "nothing relevant")
        compiled = re.compile("absent_pattern")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert text == "No matches found."
        assert metadata["pattern_preview"] == "absent_pattern"
        assert metadata["path_filter_count"] == 0
        assert metadata["match_count"] == 0
        assert metadata["truncated"] is False
        assert metadata["grep_enabled"] is True

    def test_matches_render_expected_text_blocks(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(conn, "c1", "a.md", "Parent", "Intro", "needle here")
        compiled = re.compile("needle")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert "File: a.md" in text
        assert "Chunk: c1" in text
        assert "Heading: Parent" in text
        assert "Line:" in text
        assert "Match: needle" in text
        assert text.rstrip().endswith("---")
        assert metadata["match_count"] == 1
        assert metadata["truncated"] is False

    def test_multiple_matches_from_one_chunk_are_capped(
        self, conn: sqlite3.Connection
    ) -> None:
        """Every hit of a chunk counts toward the cap, so one chunk can fill it (REQ-006)."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "needle a\nneedle b\nneedle c")
        compiled = re.compile("needle")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=2,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert metadata["match_count"] == 2
        assert metadata["truncated"] is True
        assert "[Truncated" in text
        assert text.count("Match: needle") == 2

    def test_returned_context_renders_around_the_match(
        self, conn: sqlite3.Connection
    ) -> None:
        """The rendered block shows the returned context lines around the match line."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "a1\nneedle here\nb1")
        compiled = re.compile("needle")
        text, _metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=1,
            ctx_after=1,
        )
        assert "  a1\nMatch: needle\n  b1" in text

    def test_empty_heading_path_omits_heading_line(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "needle here")
        compiled = re.compile("needle")
        text, _metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert "Heading:" not in text

    def test_path_filter_restricts_rows(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "needle here")
        _insert_chunk(conn, "c2", "b.md", "", "Intro", "needle here too")
        compiled = re.compile("needle")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=["a.md"],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert "File: a.md" in text
        assert "File: b.md" not in text
        assert metadata["path_filter_count"] == 1
        assert metadata["match_count"] == 1

    def test_truncates_at_max_matches_cap(self, conn: sqlite3.Connection) -> None:
        for i in range(5):
            _insert_chunk(conn, f"c{i}", f"f{i}.md", "", "Intro", "needle here")
        compiled = re.compile("needle")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=2,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert metadata["match_count"] == 2
        assert metadata["truncated"] is True
        assert "[Truncated" in text
        assert "cap of 2 matches reached" in text

    def test_no_truncation_message_when_under_cap(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "needle here")
        compiled = re.compile("needle")
        text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert metadata["truncated"] is False
        assert "[Truncated" not in text

    def test_pattern_preview_truncated_to_80_chars(
        self, conn: sqlite3.Connection
    ) -> None:
        long_pattern = "a" * 200
        compiled = re.compile(long_pattern)
        _text, metadata = grep_docs(
            conn,
            compiled,
            req_paths=[],
            max_matches=10,
            max_chars=200,
            ctx_before=0,
            ctx_after=0,
        )
        assert metadata["pattern_preview"] == long_pattern[:80]
        assert len(metadata["pattern_preview"]) == 80
