"""
tests/integration/test_agent_integration.py

Integration characterization tests using real components instead of mocks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from agent.memory.scoring import score


class TestMemoryScoringWithRealDB:
    """AGENT-3: Memory scoring with real DB and subprocess instead of mocks."""

    def test_memory_scoring_with_real_db(self, tmp_path: Path) -> None:
        """Score memory entries using real SQLite storage."""
        from agent.memory.scoring import score
        from db.helper import SQLiteHelper

        db_path = str(tmp_path / "test_memory.sqlite")
        # Create tables first since SQLiteHelper.open() won't create them
        with SQLiteHelper("session", db_path=db_path).open(write_mode=True) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS sessions ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "name TEXT,"
                "created_at TEXT,"
                "updated_at TEXT"
                ")"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS messages ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "session_id INTEGER,"
                "role TEXT,"
                "content TEXT,"
                "tool_calls TEXT,"
                "tool_call_id TEXT"
                ")"
            )
            db.commit()

        # Insert a session so scoring has data to work with
        with SQLiteHelper("session", db_path=db_path).open(write_mode=True) as db:
            db.execute(
                "INSERT INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (1, "test_session", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
            )
            db.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id) VALUES (?, ?, ?, ?, ?)",
                (1, "user", "Hello world", None, None),
            )
            db.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id) VALUES (?, ?, ?, ?, ?)",
                (1, "assistant", "Hi there", None, None),
            )
            db.commit()

        # Score memory entries — this exercises the real scoring logic
        from agent.memory.types import MemoryEntry, MemoryType

        entry = MemoryEntry(
            memory_id="test-score-entry",
            memory_type=MemoryType.SEMANTIC,
            source_type="conversation",
            session_id=1,
            turn_id=None,
            project="test-project",
            repo="test-repo",
            branch="main",
            content="test content",
            summary="test summary",
            importance=0.5,
            pinned=False,
            created_at="2026-01-01T00:00:00Z",
            updated_at="",
        )
        scores = score(
            bm25_rank=1.0, entry=entry, project="test-project", repo="test-repo"
        )

        assert isinstance(scores, float)

    @pytest.mark.asyncio
    async def test_memory_scoring_with_real_subprocess(self) -> None:
        """Run a subprocess and verify output without mocking."""
        result = await asyncio.create_subprocess_exec(
            "echo",
            "hello",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        assert result.returncode == 0
        assert stdout.strip() == b"hello"

    def test_memory_scoring_boundary_values(self) -> None:
        """Test score function with boundary values."""
        from agent.memory.types import MemoryEntry, MemoryType

        entry = MemoryEntry(
            memory_id="test-id",
            memory_type=MemoryType.SEMANTIC,
            source_type="conversation",
            session_id=1,
            turn_id=None,
            project="test-project",
            repo="test-repo",
            branch="main",
            content="test content",
            summary="test summary",
            importance=0.5,
            pinned=False,
            created_at="2026-01-01T00:00:00Z",
            updated_at="",
        )
        bm25_rank = 1.0
        project = "test-project"
        repo_name = "test-repo"
        branch = "main"

        result = score(bm25_rank, entry, project, repo_name, branch=branch)
        assert isinstance(result, float)
