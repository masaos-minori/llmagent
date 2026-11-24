"""Real-database tests for Memory vector storage on the session connection.

The schema is created through a default-opened ``SQLiteHelper("session")`` so these
tests fail when the session default stops loading sqlite-vec. Unit tests elsewhere
model ``memories_vec`` as a plain table, which hides vec0 behavior. The interrupted
rebuild case asserts the rollback against this real table, so it cannot be modeled.
"""

from __future__ import annotations

import sqlite3
import struct
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.memory import count_ops, write_ops
from agent.memory.retriever import HybridRetriever, VectorRetriever
from agent.memory.store import MemoryStore
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
def vec_session_db(tmp_path: Path) -> DbConfig:
    """Session DB created through a default-opened helper (no explicit load_vec)."""
    cfg = _config(tmp_path, _VEC_SO)
    with SQLiteHelper("session", db_config=cfg).open(write_mode=True) as db:
        db.executescript(build_session_schema_sql(_DIMS))
    return cfg


def _seed(cfg: DbConfig) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"),
        [0.1, 0.2, 0.3, 0.4],
        _DIMS,
        db_config=cfg,
    )
    write_ops.add(
        _entry("m2", MemoryType.EPISODIC, "dev"),
        [0.9, 0.8, 0.7, 0.6],
        _DIMS,
        db_config=cfg,
    )
    write_ops.add(
        _entry("m3", MemoryType.SEMANTIC, "dev"),
        [0.2, 0.2, 0.3, 0.4],
        _DIMS,
        db_config=cfg,
    )


def test_session_default_connection_loads_vec(vec_session_db: DbConfig) -> None:
    with SQLiteHelper("session", db_config=vec_session_db).open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
    assert rows[0][0] == 0


def test_add_and_count_vec(vec_session_db: DbConfig) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"),
        [0.1, 0.2, 0.3, 0.4],
        _DIMS,
        db_config=vec_session_db,
    )
    assert count_ops.count_vec(db_config=vec_session_db) == 1


def test_upsert_replaces_vec_row(vec_session_db: DbConfig) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"),
        [0.1, 0.2, 0.3, 0.4],
        _DIMS,
        db_config=vec_session_db,
    )
    write_ops.upsert(
        _entry("m1", MemoryType.SEMANTIC, "main"),
        [0.9, 0.9, 0.9, 0.9],
        _DIMS,
        db_config=vec_session_db,
    )
    assert count_ops.count_vec(db_config=vec_session_db) == 1
    hits = VectorRetriever(db_config=vec_session_db).knn_search(
        [0.9, 0.9, 0.9, 0.9], None, 5
    )
    assert [h.entry.memory_id for h in hits] == ["m1"]
    assert hits[0].score == pytest.approx(0.0, abs=1e-5)


def test_delete_removes_vec_row(vec_session_db: DbConfig) -> None:
    write_ops.add(
        _entry("m1", MemoryType.SEMANTIC, "main"),
        [0.1, 0.2, 0.3, 0.4],
        _DIMS,
        db_config=vec_session_db,
    )
    with patch("agent.memory.write_ops._emit_delete_event"):
        result = write_ops.delete("m1", db_config=vec_session_db)
    assert result.count == 1
    assert result.verified is True
    assert count_ops.count_vec(db_config=vec_session_db) == 0


def test_knn_search_returns_nearest_with_filters(vec_session_db: DbConfig) -> None:
    _seed(vec_session_db)
    retriever = VectorRetriever(db_config=vec_session_db)
    query = [0.1, 0.2, 0.3, 0.4]
    nearest = retriever.knn_search(query, None, 5)
    assert [h.entry.memory_id for h in nearest] == ["m1", "m3", "m2"]
    by_type = retriever.knn_search(query, "semantic", 5)
    assert [h.entry.memory_id for h in by_type] == ["m1", "m3"]
    # The branch filter keeps entries on the branch or with an empty branch.
    by_branch = retriever.knn_search(query, None, 5, branch="main")
    assert [h.entry.memory_id for h in by_branch] == ["m1"]


def test_hybrid_search_reports_hybrid_mode(vec_session_db: DbConfig) -> None:
    _seed(vec_session_db)
    retriever = HybridRetriever(db_config=vec_session_db)
    hits = retriever.search(MemoryQuery(query="alpha"), embedding=[0.1, 0.2, 0.3, 0.4])
    assert retriever.last_retrieval_mode == "hybrid"
    assert hits


class _RefusedAfterStopHelper:
    """Mirrors `helper.interrupt_when`'s contract against a real connection.

    The progress handler only fires after `check_every` VM steps, so a single short statement
    cannot be stopped deterministically on a real connection; this wrapper refuses the next
    statement the run reaches once the event is set, which is the contract the store accessor
    depends on. The run is driven through `after_statement`, so a test can stop it after the
    write and before the commit, which is what makes the rollback observable.
    """

    def __init__(self, helper: SQLiteHelper) -> None:
        self._helper = helper
        self._stop: threading.Event | None = None
        self.after_statement: Callable[[str], None] | None = None

    def open(self, **kwargs: object) -> _RefusedAfterStopHelper:
        self._helper.open(**kwargs)
        return self

    def __enter__(self) -> _RefusedAfterStopHelper:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._helper.__exit__(*_exc)

    def interrupt_when(self, stop: threading.Event, *, check_every: int = 1000) -> None:
        self._stop = stop

    def _refuse_if_stopped(self) -> None:
        if self._stop is not None and self._stop.is_set():
            raise sqlite3.OperationalError("interrupted")

    def _record(self, sql: str) -> None:
        if self.after_statement:
            self.after_statement(sql)

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        self._refuse_if_stopped()
        cur = self._helper.execute(sql, params)
        self._record(sql)
        return cur

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        self._refuse_if_stopped()
        rows = self._helper.fetchall(sql, params)
        self._record(sql)
        return rows

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._refuse_if_stopped()
        self._helper.execute("BEGIN IMMEDIATE")
        try:
            yield
            # The commit is the next statement the run reaches after its write.
            self._refuse_if_stopped()
            self._helper.execute("COMMIT")
        except BaseException:
            try:
                self._helper.execute("ROLLBACK")
            except Exception:  # noqa: BLE001 — rollback-on-error is best-effort; must not mask the original exception being re-raised
                pass
            raise


def test_interrupted_rebuild_leaves_the_vector_table_unchanged(
    vec_session_db: DbConfig,
) -> None:
    """An interrupted run reports no count and leaves the index as it was (REQ-006).

    The run is stopped between its write and the commit, so the rollback is what the test
    observes: the orphan row the run would have removed is still there.
    """
    _seed(vec_session_db)
    orphan_embedding = bytes(struct.pack("<4f", 0.5, 0.5, 0.5, 0.5))
    with SQLiteHelper("session", db_config=vec_session_db).open(write_mode=True) as db:
        db.execute(
            "INSERT INTO memories_vec(memory_id, embedding) VALUES (?, ?)",
            ("orphan", orphan_embedding),
        )
        db.commit()
    before = count_ops.count_vec(db_config=vec_session_db)
    assert before == 4

    stop = threading.Event()
    helper = _RefusedAfterStopHelper(SQLiteHelper("session", db_config=vec_session_db))
    # Stop the run after its delete, before the commit.
    helper.after_statement = lambda sql: (
        stop.set() if sql.startswith("DELETE") else None
    )
    with patch("agent.memory.store.SQLiteHelper", return_value=helper):
        result = MemoryStore(db_config=vec_session_db).reindex("vec", stop=stop)

    assert result.interrupted is True
    assert result.count == 0
    assert result.verified is False
    assert count_ops.count_vec(db_config=vec_session_db) == before


def test_missing_extension_config_fails_visibly(vec_session_db: DbConfig) -> None:
    """With no sqlite_vec_so the vec write raises and the whole write rolls back."""
    no_vec = replace(vec_session_db, sqlite_vec_so="")
    with pytest.raises(sqlite3.OperationalError):
        write_ops.add(
            _entry("m1", MemoryType.SEMANTIC, "main"),
            [0.1, 0.2, 0.3, 0.4],
            _DIMS,
            db_config=no_vec,
        )
    with pytest.raises(sqlite3.OperationalError):
        count_ops.count_vec(db_config=no_vec)
    with SQLiteHelper("session", db_config=no_vec).open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories")
    assert rows[0][0] == 0
