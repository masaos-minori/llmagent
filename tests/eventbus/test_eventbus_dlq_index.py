"""tests/test_eventbus_dlq_index.py — DLQ index regression tests."""

from __future__ import annotations

import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8017,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        auth_token="test-token",
        publisher_token="publisher-token",
        consumer_token="consumer-token",
        consumer_authorization={"consumer-A": ["test.topic"]},
        operator_token="operator-token",
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer test-token"
        yield c


def _event(topic: str = "test.topic") -> dict[str, Any]:
    return {
        # UUID v4 required by the envelope schema (else /publish returns 422).
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def _canonical_index_names(conn: Any) -> set[str]:
    rows = conn.execute(
        'SELECT name FROM sqlite_master WHERE type="index" AND tbl_name="events"'
    ).fetchall()
    return {name for (name,) in rows}


def _assert_canonical_dlq_indexes(conn: Any) -> None:
    """REQ-002: both canonical DLQ indexes exist on the examined connection."""
    indexes = _canonical_index_names(conn)
    assert "idx_events_dlq_at" in indexes, (
        f"missing idx_events_dlq_at: {sorted(indexes)}"
    )
    assert "idx_events_dlq_seq" in indexes, (
        f"missing idx_events_dlq_seq: {sorted(indexes)}"
    )


def _seed_dlq_row(client: TestClient) -> None:
    """Publish and nack one event so it lands in the DLQ for the plan assertion."""
    pub_headers = {"Authorization": "Bearer publisher-token"}
    r = client.post("/publish", json=_event(), headers=pub_headers)
    assert r.status_code == 200  # REQ-004: setup publish is authorised
    con = cast(FastAPI, client.app).state.db
    assert con is not None
    con.execute(
        "UPDATE events SET dlq_at = ? WHERE topic = ?",
        ("2026-10-28T00:00:00Z", "test.topic"),
    )
    con.commit()


def test_dlq_index_shape_present(client: TestClient) -> None:
    """REQ-002: canonical DLQ indexes present under the open_db schema; no DDL runs."""
    assert cast(FastAPI, client.app).state.db is not None
    _assert_canonical_dlq_indexes(cast(FastAPI, client.app).state.db)


def test_dlq_index_shape_fails_when_dropped(client: TestClient) -> None:
    """REQ-002 negative: dropping a canonical index in a throwaway copy is detected."""
    import tempfile
    from pathlib import Path

    con = cast(FastAPI, client.app).state.db
    assert con is not None
    # PRAGMA database_file is empty on the pragma-configured shared connection;
    # config.db_path is the authoritative path to the same live test DB file.
    db_path = cast(FastAPI, client.app).state.config.db_path
    with tempfile.TemporaryDirectory() as tmp:
        copy_path = Path(tmp) / "copy.sqlite"
        shutil.copyfile(db_path, copy_path)
        copy_conn = sqlite3.connect(copy_path)
        try:
            copy_conn.execute("DROP INDEX IF EXISTS idx_events_dlq_at")
            with pytest.raises(AssertionError):
                _assert_canonical_dlq_indexes(copy_conn)
        finally:
            copy_conn.close()


def test_dlq_index_plan_matches_production_sql(client: TestClient) -> None:
    """REQ-003: EXPLAIN the exact SQL fetch_dlq()/count_dlq() execute."""
    from eventbus.event_repo import count_dlq, fetch_dlq

    con = cast(FastAPI, client.app).state.db
    assert con is not None
    # Seed one DLQ row so fetch_dlq returns something.
    _seed_dlq_row(client)

    captured: list[str] = []
    con.set_trace_callback(captured.append)
    try:
        count_dlq(con)
        fetch_dlq(con, limit=2, offset=0)
    finally:
        con.set_trace_callback(None)

    count_sql = next(s for s in captured if s.startswith("SELECT COUNT(*)"))
    page_sql = next(
        s for s in captured if s.startswith("SELECT") and "ORDER BY seq" in s
    )

    count_plan = con.execute(f"EXPLAIN QUERY PLAN {count_sql}").fetchall()
    page_plan = con.execute(f"EXPLAIN QUERY PLAN {page_sql}").fetchall()

    # EXPLAIN QUERY PLAN returns sqlite3.Row objects; str(Row) is only the object
    # repr, so render the values before matching the plan text.
    count_text = " ".join(" ".join(str(v) for v in row) for row in count_plan)
    page_text = " ".join(" ".join(str(v) for v in row) for row in page_plan)

    assert "idx_events_dlq_seq" in count_text, count_plan
    assert "sort" not in page_text.lower(), page_plan
