"""Real-database tests for Memory vector storage on the session connection.

The schema is created through a default-opened ``SQLiteHelper("session")`` so these
tests fail when the session default stops loading sqlite-vec. Unit tests elsewhere
model ``memories_vec`` as a plain table, which hides vec0 behavior.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.memory import count_ops, write_ops
from agent.memory.retriever import HybridRetriever, VectorRetriever
from agent.memory.types import MemoryEntry, MemoryQuery, MemoryType, SourceType
from db.config import DbConfig
from db.helper import SQLiteHelper
from db.schema_sql import build_session_schema_sql

_VEC_SO = "/opt/llm/sqlite-vec/vec0.so"
_DIMS = 4

pytestmark = pytest.mark.skipif(
    not Path(_VEC_SO).exists(),
    reason="sqlite-vec extension not installed at /opt/llm/sqlite-vec/vec0.so",
)


def _config(tmp_path: Path, vec_so: str) -> DbConfig:
    return DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=str(tmp_path / "session.sqlite"),
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
        eventbus_db_path=str(tmp_path / "eventbus.sqlite"),
        sqlite_vec_so=vec_so,
    )


def _entry(memory_id: str, memory_type: MemoryType, branch: str) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id,
        memory_type=memory_type,
        source_type=SourceType.DECISION,
        session_id=None,
        turn_id=None,
        project="p",
        repo="r",
        branch=branch,
        content=f"alpha beta {memory_id}",
        summary=f"summary {memory_id}",
    )


@pytest.fixture
def vec_session_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Session DB created through a default-opened helper (no explicit load_vec)."""
    cfg = _config(tmp_path, _VEC_SO)
    monkeypatch.setattr("db.helper.build_db_config", lambda: cfg)
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.executescript(build_session_schema_sql(_DIMS))
    return tmp_path


def _seed() -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"), [0.1, 0.2, 0.3, 0.4], _DIMS
    )
    write_ops.add(_entry("m2", MemoryType.EPISODIC, "dev"), [0.9, 0.8, 0.7, 0.6], _DIMS)
    write_ops.add(_entry("m3", MemoryType.SEMANTIC, "dev"), [0.2, 0.2, 0.3, 0.4], _DIMS)


def test_session_default_connection_loads_vec(vec_session_db: Path) -> None:
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
    assert rows[0][0] == 0


def test_add_and_count_vec(vec_session_db: Path) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"), [0.1, 0.2, 0.3, 0.4], _DIMS
    )
    assert count_ops.count_vec() == 1


def test_upsert_replaces_vec_row(vec_session_db: Path) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"), [0.1, 0.2, 0.3, 0.4], _DIMS
    )
    write_ops.upsert(
        _entry("m1", MemoryType.SEMANTIC, "main"), [0.9, 0.9, 0.9, 0.9], _DIMS
    )
    assert count_ops.count_vec() == 1
    hits = VectorRetriever().knn_search([0.9, 0.9, 0.9, 0.9], None, 5)
    assert [h.entry.memory_id for h in hits] == ["m1"]
    assert hits[0].score == pytest.approx(0.0, abs=1e-5)


def test_delete_removes_vec_row(vec_session_db: Path) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"), [0.1, 0.2, 0.3, 0.4], _DIMS
    )
    with patch("agent.memory.write_ops._emit_delete_event"):
        assert write_ops.delete("m1") is True
    assert count_ops.count_vec() == 0


def test_knn_search_returns_nearest_with_filters(vec_session_db: Path) -> None:
    _seed()
    retriever = VectorRetriever()
    query = [0.1, 0.2, 0.3, 0.4]
    nearest = retriever.knn_search(query, None, 5)
    assert [h.entry.memory_id for h in nearest] == ["m1", "m3", "m2"]
    by_type = retriever.knn_search(query, "semantic", 5)
    assert [h.entry.memory_id for h in by_type] == ["m1", "m3"]
    # The branch filter keeps entries on the branch or with an empty branch.
    by_branch = retriever.knn_search(query, None, 5, branch="main")
    assert [h.entry.memory_id for h in by_branch] == ["m1"]


def test_hybrid_search_reports_hybrid_mode(vec_session_db: Path) -> None:
    _seed()
    retriever = HybridRetriever()
    hits = retriever.search(MemoryQuery(query="alpha"), embedding=[0.1, 0.2, 0.3, 0.4])
    assert retriever.last_retrieval_mode == "hybrid"
    assert hits


def test_missing_extension_config_fails_visibly(
    vec_session_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no sqlite_vec_so the vec write raises and the whole write rolls back."""
    no_vec = _config(vec_session_db, "")
    monkeypatch.setattr("db.helper.build_db_config", lambda: no_vec)
    with pytest.raises(sqlite3.OperationalError):
        write_ops.add(
            _entry("m1", MemoryType.SEMANTIC, "main"), [0.1, 0.2, 0.3, 0.4], _DIMS
        )
    with pytest.raises(sqlite3.OperationalError):
        count_ops.count_vec()
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories")
    assert rows[0][0] == 0
