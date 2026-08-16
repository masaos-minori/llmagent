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
    def test_returns_none_when_no_match(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Title", "nothing relevant here")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("xyz_not_present")
        assert (
            find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
            is None
        )

    def test_returns_match_on_first_line(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "hello world")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("world")
        match = find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
        assert match is not None
        assert match.chunk_id == "c1"
        assert match.source_path == "a.md"
        assert match.heading_path == ""
        assert match.match_text == "world"
        # Full text is "Intro\nhello world" -> match is on line index 1 (0-based) -> line_number 2
        assert match.line_number == 2

    def test_matches_within_heading_line(self, conn: sqlite3.Connection) -> None:
        """A pattern that only matches the synthesized heading line (row['heading'])
        is found on line 1, since full_text = f"{heading}\\n{content}"."""
        _insert_chunk(conn, "c1", "a.md", "Parent", "UniqueHeading", "content body")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("UniqueHeading")
        match = find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
        assert match is not None
        assert match.line_number == 1
        assert match.heading_path == "Parent"

    def test_match_text_truncated_to_max_chars(self, conn: sqlite3.Connection) -> None:
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "aaaaaaaaaa")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("a+")
        match = find_grep_match(row, compiled, max_chars=3, ctx_before=0, ctx_after=0)
        assert match is not None
        assert match.match_text == "aaa"

    def test_only_first_match_in_row_is_returned(
        self, conn: sqlite3.Connection
    ) -> None:
        """`find_grep_match` returns on the first `finditer` hit even if more exist."""
        _insert_chunk(conn, "c1", "a.md", "", "Intro", "foo foo foo")
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("foo")
        match = find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
        assert match is not None
        assert match.line_number == 2

    def test_line_number_for_match_on_later_line(
        self, conn: sqlite3.Connection
    ) -> None:
        _insert_chunk(
            conn, "c1", "a.md", "", "Intro", "line one\nline two\ntarget line"
        )
        row = conn.execute("SELECT * FROM chunks").fetchone()
        compiled = re.compile("target")
        match = find_grep_match(row, compiled, max_chars=200, ctx_before=0, ctx_after=0)
        assert match is not None
        # full_text lines: ["Intro", "line one", "line two", "target line"] -> index 3 -> line 4
        assert match.line_number == 4


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
