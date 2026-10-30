"""tests/test_eventbus_dlq_outbox.py
dlqbox001 outbox worker crash-window suite (REQ-004-REQ-006, REQ-009; AC-3/AC-4).

Every test drives process_outbox directly with a synchronous run_locked stand-in
so no test waits on wall-clock time. Faults are injected with monkeypatch at the
os.replace boundary inside eventbus.dlq.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any

import orjson
import pytest
from fastapi.testclient import TestClient

from tests.eventbus.eventbus_helpers import eventbus_auth_headers, eventbus_test_tokens


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    async def _no_loop(app: Any) -> None:
        """Disable the periodic dlq_loop: this suite drives process_outbox explicitly.

        The worker contract is the subject of these tests; a live loop cycle would
        race with the fault injection and the direct worker calls.
        """

    monkeypatch.setattr(eb_app, "_dlq_loop", _no_loop)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = eventbus_auth_headers("publisher")["Authorization"]
        yield c


def _event(topic: str = "t") -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-01-01T00:00:00Z",
    }


def _base_cfg(deadletter_dir: str, **overrides: Any) -> Any:
    from eventbus.config import EventBusConfig

    cfg: Any = EventBusConfig(
        port=8015,
        db_path=str(Path(deadletter_dir).parent / "eventbus.sqlite"),
        storage_dir=str(Path(deadletter_dir).parent / "storage"),
        deadletter_dir=deadletter_dir,
        max_retry=2,
        **eventbus_test_tokens("test-token"),
        **overrides,
    )
    return cfg


def _worker(db: Any, deadletter_dir: str, cfg: Any = None) -> dict[str, int]:
    """Run one synchronous process_outbox cycle (stand-in for the dlq_loop tick)."""
    from eventbus.dlq import process_outbox

    cfg = cfg or _base_cfg(deadletter_dir)

    async def _runner(fn: Any) -> Any:
        return fn()

    result: dict[str, int] = asyncio.run(process_outbox(db, deadletter_dir, cfg, _runner))
    return result


def _promote(db: Any, deadletter_dir: str, event_id: str) -> None:
    """Promote an event via the DB-only promotion path (gating already seeded)."""
    from eventbus.dlq import promote_single

    assert promote_single(db, deadletter_dir, event_id) is True


def _make_promotable(db: Any, event_id: str) -> None:
    db.execute(
        "INSERT INTO consumer_delivery (consumer_id, event_id, acked, consumer_delivery_failure_count) VALUES (?, ?, 0, 2)",
        ("consumer-A", event_id),
    )
    db.commit()


def _advance_clock(db: Any) -> None:
    """Mark all pending rows due now (deterministic stand-in for backoff elapsing)."""
    from eventbus.dlq import now_iso

    db.execute(
        "UPDATE dlq_outbox SET next_attempt_at = ? WHERE status = 'pending'",
        (now_iso(),),
    )
    db.commit()


def _outbox_row(db: Any, event_id: str) -> Any:
    return db.execute(
        "SELECT status, attempts, last_error, next_attempt_at, completed_at"
        " FROM dlq_outbox WHERE event_id = ?",
        (event_id,),
    ).fetchone()


def _counter(name: str) -> float:
    """Current value of a dlq counter, registering its collector if needed."""
    from eventbus import dlq
    from prometheus_client import REGISTRY

    collectors = {
        "eventbus_dlq_outbox_generated_total": dlq._dlq_outbox_generated_counter,
        "eventbus_dlq_outbox_attempt_failure_total": (
            dlq._dlq_outbox_attempt_failure_counter
        ),
        "eventbus_dlq_outbox_failed_total": dlq._dlq_outbox_failed_counter,
    }
    collector = collectors[name]
    if collector not in REGISTRY._collector_to_names:
        try:
            REGISTRY.register(collector)
        except ValueError:
            pass
    value: float = REGISTRY.get_sample_value(name) or 0.0
    return value


def test_commit_then_crash_before_file(client: TestClient, tmp_path: Path) -> None:
    """REQ-04/AC-3: the committed pending row survives; the next cycle generates the file.

    The crash window between the promotion commit and artifact generation leaves
    only a pending outbox row; re-running the worker (the restart analogue,
    in-process) completes it.
    """
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200

    for key in ("crash-window-nack-1", "crash-window-nack-2"):
        r = client.post(
            f"/nack?event_id={ev['event_id']}&consumer_id=test-consumer"
            f"&idempotency_key={key}",
            headers=eventbus_auth_headers("consumer"),
        )
        assert r.status_code == 200
    assert r.json().get("dlq_promoted") is True

    row = _outbox_row(db, ev["event_id"])
    assert row["status"] == "pending"
    assert not (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()

    generated_before = _counter("eventbus_dlq_outbox_generated_total")
    report = _worker(db, str(tmp_path / "deadletter"))
    assert report == {"processed": 1, "generated": 1, "failed_attempts": 0, "terminal_failed": 0}
    assert _counter("eventbus_dlq_outbox_generated_total") - generated_before == 1

    target = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert target.exists()
    record = orjson.loads(target.read_bytes())
    assert record["event_id"] == ev["event_id"]
    row = _outbox_row(db, ev["event_id"])
    assert row["status"] == "done"
    assert row["completed_at"] is not None


def test_crash_during_tmp_write_leaves_interrupted_tmp(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crash between the tmp write and the rename leaves a .dlq_tmp_* the reconcile counts.

    os.replace AND the tmp cleanup are made to fail for this event, simulating the
    process dying after the tmp file exists but before rename or cleanup. The
    outbox row records the failed attempt; reconcile reports interrupted_tmp.
    """
    from eventbus import dlq
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200
    _make_promotable(db, ev["event_id"])
    _promote(db, deadletter, ev["event_id"])

    original_replace = os.replace
    original_unlink = os.unlink

    def _fail_replace(src: str, dst: str) -> None:
        if os.path.basename(dst) == f"{ev['event_id']}.json":
            raise OSError("simulated crash during rename")
        original_replace(src, dst)

    def _fail_unlink(path: Any) -> None:
        if ".dlq_tmp_" in str(path):
            raise OSError("simulated cleanup failure")
        original_unlink(path)

    monkeypatch.setattr(dlq.os, "replace", _fail_replace)
    monkeypatch.setattr(dlq.os, "unlink", _fail_unlink)

    report = _worker(db, deadletter)
    assert report["failed_attempts"] == 1
    row = _outbox_row(db, ev["event_id"])
    assert row["status"] == "pending"
    assert row["attempts"] == 1
    assert "simulated" in str(row["last_error"])

    leftovers = list(Path(deadletter).glob(".dlq_tmp_*"))
    assert len(leftovers) == 1

    monkeypatch.undo()  # the process "restarts": writer restored for the reconcile phase

    reconciled = reconcile_missing_dlq_files(db, deadletter)
    assert reconciled["interrupted_tmp"] == 1
    assert reconciled["rebuilt"] == 1  # the missing artifact is rebuilt from the DB row
    assert (Path(deadletter) / f"{ev['event_id']}.json").exists()
    assert leftovers[0].exists()  # report-only: reconcile does not remove leftovers


def test_one_failing_artifact_does_not_block_others(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-005/AC-4: per-event isolation — B completes while A records a bounded attempt."""
    from eventbus import dlq
    from eventbus.db import open_db
    from eventbus.dlq import now_iso

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    ev_a = _event("iso-a")
    ev_b = _event("iso-b")
    for ev in (ev_a, ev_b):
        assert client.post("/publish", json=ev).status_code == 200
        _make_promotable(db, ev["event_id"])
        _promote(db, deadletter, ev["event_id"])

    original_replace = os.replace

    def _fail_for_a(src: str, dst: str) -> None:
        if os.path.basename(dst) == f"{ev_a['event_id']}.json":
            raise OSError("disk full for A")
        original_replace(src, dst)

    monkeypatch.setattr(dlq.os, "replace", _fail_for_a)

    report = _worker(db, deadletter)
    assert report["processed"] == 2
    assert report["generated"] == 1
    assert report["failed_attempts"] == 1

    assert (Path(deadletter) / f"{ev_b['event_id']}.json").exists()
    assert not (Path(deadletter) / f"{ev_a['event_id']}.json").exists()

    row_a = _outbox_row(db, ev_a["event_id"])
    assert row_a["status"] == "pending"
    assert row_a["attempts"] == 1
    assert "disk full for A" in str(row_a["last_error"])
    assert str(row_a["next_attempt_at"]) > now_iso()  # exponential backoff scheduled

    row_b = _outbox_row(db, ev_b["event_id"])
    assert row_b["status"] == "done"


def test_terminal_failed_after_bound(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-005: attempts are bounded by outbox_max_attempts; the row turns terminal 'failed'."""
    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    cfg = _base_cfg(deadletter, outbox_max_attempts=3)
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200
    _make_promotable(db, ev["event_id"])
    _promote(db, deadletter, ev["event_id"])

    original_replace = os.replace

    def _always_fail(src: str, dst: str) -> None:
        raise OSError("persistent disk failure")

    monkeypatch.setattr(dlq.os, "replace", _always_fail)

    attempt_before = _counter("eventbus_dlq_outbox_attempt_failure_total")
    terminal_before = _counter("eventbus_dlq_outbox_failed_total")

    for cycle in range(3):
        _advance_clock(db)
        report = _worker(db, deadletter, cfg)
        assert report == {
            "processed": 1,
            "generated": 0,
            "failed_attempts": 1,
            "terminal_failed": 1 if cycle == 2 else 0,
        }
        row = _outbox_row(db, ev["event_id"])
        assert row["attempts"] == cycle + 1
        expected_status = "pending" if cycle < 2 else "failed"
        assert row["status"] == expected_status

    assert _counter("eventbus_dlq_outbox_attempt_failure_total") - attempt_before == 3
    assert _counter("eventbus_dlq_outbox_failed_total") - terminal_before == 1

    # Terminal rows are never fetched again, even with the writer restored.
    monkeypatch.setattr(dlq.os, "replace", original_replace)
    _advance_clock(db)
    report = _worker(db, deadletter, cfg)
    assert report == {"processed": 0, "generated": 0, "failed_attempts": 0, "terminal_failed": 0}
    assert not (Path(deadletter) / f"{ev['event_id']}.json").exists()


def test_restart_with_pending_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-006/AC-3: a fresh lifespan with a fresh connection processes pending rows."""
    import eventbus.app as eb_app
    from eventbus.config import EventBusConfig
    from eventbus.db import open_db

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
        **eventbus_test_tokens("test-token"),
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    ev = _event()
    db1 = open_db(str(tmp_path / "eventbus.sqlite"))

    async def _no_loop(app: Any) -> None:
        """Suspend the periodic loop: the test drives the first cycle explicitly."""

    with TestClient(eb_app.app) as c1:
        c1.headers["Authorization"] = eventbus_auth_headers("publisher")["Authorization"]
        assert c1.post("/publish", json=ev).status_code == 200
        _make_promotable(db1, ev["event_id"])
        _promote(db1, str(tmp_path / "deadletter"), ev["event_id"])
        assert _outbox_row(db1, ev["event_id"])["status"] == "pending"

    # Shut down (dlq_task is joined on lifespan shutdown) and start a new lifespan:
    # the pending row survives; the first explicit cycle on a fresh connection
    # processes it. The periodic loop is suspended so the cycle is test-driven.
    monkeypatch.setattr(eb_app, "_dlq_loop", _no_loop)
    with TestClient(eb_app.app) as c2:
        db2 = open_db(str(tmp_path / "eventbus.sqlite"))
        assert _outbox_row(db2, ev["event_id"])["status"] == "pending"
        report = _worker(db2, str(tmp_path / "deadletter"))
        assert report["generated"] == 1
        assert _outbox_row(db2, ev["event_id"])["status"] == "done"
        assert (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()
        assert c2 is not None  # lifespan active during the cycle


def test_idempotent_reprocessing_no_rewrite(
    client: TestClient, tmp_path: Path
) -> None:
    """A done artifact that is already canonical completes without touching the file."""
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200
    _make_promotable(db, ev["event_id"])
    _promote(db, deadletter, ev["event_id"])

    report = _worker(db, deadletter)
    assert report["generated"] == 1

    target = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    content_before = target.read_bytes()
    stat_before = target.stat()

    # Simulate a crash between the artifact write and the done mark: the row goes
    # back to pending while the canonical file is already in place.
    db.execute(
        "UPDATE dlq_outbox SET status = 'pending', next_attempt_at = NULL, completed_at = NULL"
        " WHERE event_id = ?",
        (ev["event_id"],),
    )
    db.commit()

    generated_before = _counter("eventbus_dlq_outbox_generated_total")
    report = _worker(db, deadletter)
    assert report["processed"] == 1
    assert report["generated"] == 0  # completion without regeneration

    assert target.read_bytes() == content_before
    stat_after = target.stat()
    assert stat_before.st_mtime_ns == stat_after.st_mtime_ns  # never rewritten
    assert _counter("eventbus_dlq_outbox_generated_total") - generated_before == 0
    assert _outbox_row(db, ev["event_id"])["status"] == "done"


def test_failed_row_never_undoes_committed_dlq_state(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-009: repeated artifact-generation failures never clear dlq_at or duplicate the event."""
    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200
    _make_promotable(db, ev["event_id"])
    _promote(db, deadletter, ev["event_id"])

    original_replace = os.replace

    def _always_fail(src: str, dst: str) -> None:
        raise OSError("persistent failure")

    monkeypatch.setattr(dlq.os, "replace", _always_fail)

    for _ in range(3):
        _advance_clock(db)
        _worker(db, deadletter)
        row = db.execute(
            "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["dlq_at"] is not None  # never rolled back by generation failures
        events = db.execute(
            "SELECT COUNT(*) AS c FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()["c"]
        assert events == 1  # generation never duplicates the event row
        assert _outbox_row(db, ev["event_id"])["status"] == "pending"

    monkeypatch.setattr(dlq.os, "replace", original_replace)
    _advance_clock(db)
    report = _worker(db, deadletter)
    assert report["generated"] == 1
    assert (Path(deadletter) / f"{ev['event_id']}.json").exists()
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is not None


def test_outbox_retry_backoff_delays_next_attempt(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-005/AC-4: after a failed attempt the row is pending and not due until the backoff window."""
    from eventbus import dlq
    from eventbus.db import open_db

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    deadletter = str(tmp_path / "deadletter")
    ev = _event()
    assert client.post("/publish", json=ev).status_code == 200
    _make_promotable(db, ev["event_id"])
    _promote(db, deadletter, ev["event_id"])

    def _always_fail(src: str, dst: str) -> None:
        raise OSError("transient failure")

    monkeypatch.setattr(dlq.os, "replace", _always_fail)

    report = _worker(db, deadletter)
    assert report == {"processed": 1, "generated": 0, "failed_attempts": 1, "terminal_failed": 0}

    row = _outbox_row(db, ev["event_id"])
    assert row["status"] == "pending"
    assert row["next_attempt_at"] is not None  # backoff window scheduled

    report = _worker(db, deadletter)  # same cycle: not due yet
    assert report == {"processed": 0, "generated": 0, "failed_attempts": 0, "terminal_failed": 0}

    _advance_clock(db)
    report = _worker(db, deadletter)
    assert report["failed_attempts"] == 1
    row = _outbox_row(db, ev["event_id"])
    assert row["status"] == "pending"  # bounded but not yet terminal (max_attempts default 5)
    assert row["attempts"] == 2
