"""
tests/test_mapper.py
Unit tests for memory/mapper.py: row_to_entry conversion.
"""

from __future__ import annotations

import sqlite3

from agent.memory.mapper import row_to_entry
from agent.memory.types import SourceType


class TestRowToEntry:
    def test_basic_dict_conversion(self) -> None:
        row = {
            "memory_id": 1,
            "memory_type": "episodic",
            "source_type": "conversation",
            "session_id": 42,
            "turn_id": "3",
            "project": "myproject",
            "repo": "myrepo",
            "branch": "main",
            "content": "some content",
            "summary": "a summary",
            "tags": '["ai", "code"]',
            "importance": 0.8,
            "pinned": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
        }
        entry = row_to_entry(row)
        assert entry.memory_id == "1"
        assert entry.memory_type == "episodic"
        assert entry.source_type == SourceType.CONVERSATION
        assert entry.session_id == 42
        assert entry.turn_id == "3"
        assert entry.project == "myproject"
        assert entry.repo == "myrepo"
        assert entry.branch == "main"
        assert entry.content == "some content"
        assert entry.summary == "a summary"
        assert entry.tags == ["ai", "code"]
        assert entry.importance == 0.8
        assert entry.pinned is True
        assert entry.created_at == "2024-01-01T00:00:00Z"
        assert entry.updated_at == "2024-01-02T00:00:00Z"

    def test_minimal_dict(self) -> None:
        row = {
            "memory_id": 1,
            "memory_type": "semantic",
            "content": "minimal",
        }
        entry = row_to_entry(row)
        assert entry.memory_id == "1"
        assert entry.memory_type == "semantic"
        assert entry.content == "minimal"
        assert entry.source_type == SourceType.CONVERSATION
        assert entry.session_id is None
        assert entry.turn_id is None
        assert entry.project == ""
        assert entry.repo == ""
        assert entry.branch == ""
        assert entry.summary == ""
        assert entry.tags == []
        assert entry.importance == 0.5
        assert entry.pinned is False
        assert entry.created_at == ""
        assert entry.updated_at == ""

    def test_corrupted_tags_json_raises(self) -> None:
        """Corrupted tags JSON raises an exception — no silent fallback to []."""
        import pytest

        row = {
            "memory_id": 2,
            "memory_type": "episodic",
            "content": "data",
            "tags": "not valid json[[[",
        }
        with pytest.raises(Exception):
            row_to_entry(row)

    def test_tags_as_list_already(self) -> None:
        row = {
            "memory_id": 3,
            "memory_type": "episodic",
            "content": "data",
            "tags": ["tag1", "tag2"],
        }
        entry = row_to_entry(row)
        assert entry.tags == ["tag1", "tag2"]

    def test_unknown_source_type_raises(self) -> None:
        """Unknown source_type raises ValueError — no silent fallback to CONVERSATION."""
        import pytest

        row = {
            "memory_id": 4,
            "memory_type": "episodic",
            "content": "data",
            "source_type": "unknown_type",
        }
        with pytest.raises(ValueError, match="Invalid source_type"):
            row_to_entry(row)

    def test_importance_default(self) -> None:
        row = {
            "memory_id": 5,
            "memory_type": "episodic",
            "content": "data",
        }
        entry = row_to_entry(row)
        assert entry.importance == 0.5

    def test_pinned_false_when_not_present_or_zero(self) -> None:
        row = {
            "memory_id": 6,
            "memory_type": "episodic",
            "content": "data",
        }
        entry = row_to_entry(row)
        assert entry.pinned is False

    def test_tags_missing_defaults_to_empty(self) -> None:
        row = {
            "memory_id": 7,
            "memory_type": "episodic",
            "content": "data",
        }
        entry = row_to_entry(row)
        assert entry.tags == []

    def test_sqlite_row_conversion(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE t (memory_id INT, memory_type TEXT,"
            " source_type TEXT, session_id INT, turn_id TEXT,"
            " project TEXT, repo TEXT, branch TEXT, content TEXT,"
            " summary TEXT, tags TEXT, importance REAL, pinned INT,"
            " created_at TEXT, updated_at TEXT)",
        )
        conn.execute(
            "INSERT INTO t VALUES (10, 'episodic', 'conversation', 1, '2',"
            " 'p', 'r', 'b', 'content', 'summary',"
            ' \'["x"]\', 0.9, 1, "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z")',
        )
        row = conn.execute("SELECT * FROM t").fetchone()
        assert row is not None
        entry = row_to_entry(row)
        assert entry.memory_id == "10"
        assert entry.memory_type == "episodic"
        assert entry.content == "content"
        assert entry.tags == ["x"]
        assert entry.importance == 0.9
        assert entry.pinned is True
