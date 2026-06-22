# Implementation: Event Bus app.py Phase 3 — DLQ promotion and /dlq endpoint

## Goal

Extend `scripts/eventbus/app.py` with a background DLQ promotion task and `GET /dlq` /
`POST /dlq/{event_id}/requeue` endpoints. After this phase: events that exceed `MAX_RETRY`
are atomically written to `deadletter/` and marked in the DB; DLQ events can be listed and
requeued via HTTP.

## Scope

**In-Scope:**
- `scripts/eventbus/app.py` — DLQ background task in `lifespan`, `/dlq`, `/dlq/{id}/requeue`
- `scripts/eventbus/dlq.py` — `promote_to_dlq()` and atomic file write logic
- `tests/test_eventbus_phase3.py`

**Out-of-Scope:**
- ACK endpoint (`acked_at` update — not required by Phase 3 spec)
- replication / multi-node DLQ sync (Phase 2+ future scope)
- `retry_count` increment logic (callers are responsible for incrementing; the bus tracks
  the count, not the retry mechanism itself)

## Assumptions

1. Phase 1 and Phase 2 are in place.
2. `retry_count` is incremented by the consumer before the bus marks an event for DLQ.
   The bus reads `retry_count >= MAX_RETRY` and promotes — it does not perform the retry.
3. Atomic file write on Linux is `os.replace(tmp, dst)` — rename is atomic on POSIX for
   same-filesystem moves.
4. DLQ background task runs every 60 seconds via `asyncio.create_task` inside `lifespan`.
5. `requeue` resets `retry_count=0` and `dlq_at=NULL`; the event re-enters the normal
   delivery stream without re-publishing.

## Implementation

### Target files

- `scripts/eventbus/dlq.py`
- `scripts/eventbus/app.py` (extend lifespan + add endpoints)
- `tests/test_eventbus_phase3.py`

### Procedure

#### Step 1: `scripts/eventbus/dlq.py`

```python
from __future__ import annotations
import json
import logging
import os
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def promote_to_dlq(
    db: sqlite3.Connection,
    deadletter_dir: str,
    max_retry: int,
) -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, retry_count"
        " FROM events WHERE retry_count >= ? AND dlq_at IS NULL",
        (max_retry,),
    ).fetchall()

    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        record = {
            "seq": row["seq"],
            "event_id": event_id,
            "topic": row["topic"],
            "payload": json.loads(row["payload"]),
            "producer": row["producer"],
            "published_at": row["published_at"],
            "retry_count": row["retry_count"],
            "dlq_at": now,
        }
        _atomic_write(deadletter_dir, event_id, record)
        db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ?",
            (now, event_id),
        )
        db.commit()
        logger.warning("dlq promoted event_id=%s retry_count=%d", event_id, row["retry_count"])
        promoted += 1

    return promoted


def _atomic_write(deadletter_dir: str, event_id: str, record: dict) -> None:
    dir_path = Path(deadletter_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    dst = dir_path / f"{event_id}.json"
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, prefix=".dlq_tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(record, f)
        os.replace(tmp_path, dst)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

Key decisions:
- `tempfile.mkstemp` in the same directory as `dst` — `os.replace` is atomic only for
  same-filesystem moves; temp in the same dir guarantees this.
- `os.fdopen(fd, "w")` takes ownership of the fd returned by `mkstemp`; no separate `close`.
- `db.commit()` is called per-row, not once at the end — if the process crashes mid-loop,
  already-promoted rows are safely in the DB and idempotent on the next run (checked via
  `dlq_at IS NULL`).

#### Step 2: `scripts/eventbus/app.py` — DLQ background task in lifespan

Extend `lifespan`:

```python
import asyncio
from eventbus.dlq import promote_to_dlq

_dlq_task: asyncio.Task | None = None
_DLQ_INTERVAL = 60.0  # seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cfg, _db, _envelope_schema, _dlq_task
    _cfg = load_config()
    _db = open_db(_cfg.db_path)
    _envelope_schema = json.loads(_ENVELOPE_SCHEMA_PATH.read_text())
    Path(_cfg.storage_dir).mkdir(parents=True, exist_ok=True)

    _dlq_task = asyncio.create_task(_dlq_loop())
    yield

    if _dlq_task:
        _dlq_task.cancel()
        try:
            await _dlq_task
        except asyncio.CancelledError:
            pass
    if _db:
        _db.close()


async def _dlq_loop() -> None:
    while True:
        try:
            n = promote_to_dlq(_db, _cfg.deadletter_dir, _cfg.max_retry)
            if n:
                logger.info("dlq_loop promoted=%d", n)
        except Exception:
            logger.exception("dlq_loop error")
        await asyncio.sleep(_DLQ_INTERVAL)
```

#### Step 3: `scripts/eventbus/app.py` — `/dlq` and `/dlq/{event_id}/requeue`

```python
@app.get("/dlq")
async def dlq_list():
    rows = _db.execute(
        "SELECT seq, event_id, topic, producer, published_at, retry_count, dlq_at"
        " FROM events WHERE dlq_at IS NOT NULL ORDER BY seq"
    ).fetchall()
    return [dict(r) for r in rows]


@app.post("/dlq/{event_id}/requeue")
async def dlq_requeue(event_id: str):
    cur = _db.execute(
        "UPDATE events SET retry_count = 0, dlq_at = NULL WHERE event_id = ?",
        (event_id,),
    )
    _db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="event not found")
    logger.info("dlq requeued event_id=%s", event_id)
    return {"event_id": event_id, "requeued": True}
```

- `requeue` does NOT delete the `deadletter/` file — it remains as a historical record.
  The reset `dlq_at=NULL` and `retry_count=0` re-expose the event to `/subscribe` consumers.

#### Step 4: `tests/test_eventbus_phase3.py`

```python
import json, uuid, pytest
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.fixture
def client(tmp_path, monkeypatch):
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=2,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic="t"):
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {},
        "producer": "p",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_dlq_promotion_when_retry_exhausted(client, tmp_path):
    from eventbus.dlq import promote_to_dlq
    from eventbus.db import open_db
    db_path = str(tmp_path / "eventbus.sqlite")
    db = open_db(db_path)

    ev = _event()
    client.post("/publish", json=ev)
    # Simulate retry exhaustion
    db.execute(
        "UPDATE events SET retry_count = 2 WHERE event_id = ?", (ev["event_id"],)
    )
    db.commit()

    n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)
    assert n == 1
    dlq_file = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    assert dlq_file.exists()
    record = json.loads(dlq_file.read_text())
    assert record["event_id"] == ev["event_id"]
    assert record["dlq_at"] is not None


def test_dlq_list(client, tmp_path):
    from eventbus.dlq import promote_to_dlq
    from eventbus.db import open_db
    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev = _event()
    client.post("/publish", json=ev)
    db.execute("UPDATE events SET retry_count=2 WHERE event_id=?", (ev["event_id"],))
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.get("/dlq")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev["event_id"] in ids


def test_dlq_requeue(client, tmp_path):
    from eventbus.dlq import promote_to_dlq
    from eventbus.db import open_db
    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev = _event()
    client.post("/publish", json=ev)
    db.execute("UPDATE events SET retry_count=2 WHERE event_id=?", (ev["event_id"],))
    db.commit()
    promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

    r = client.post(f"/dlq/{ev['event_id']}/requeue")
    assert r.status_code == 200
    assert r.json()["requeued"] is True

    r2 = client.get("/dlq")
    ids = [e["event_id"] for e in r2.json()]
    assert ev["event_id"] not in ids
```

### Method

- `dlq.py` is a pure-function module (no FastAPI dependency) — testable without spinning up
  the full app; tests call `promote_to_dlq` directly with a real SQLite connection.
- `os.replace(tmp, dst)` POSIX atomic rename — if the process crashes between `mkstemp` and
  `replace`, the temp file is left orphaned but the DB row is unchanged (`dlq_at IS NULL`),
  so the next DLQ loop run retries the promotion safely.
- `max_retry=2` in test fixture (instead of 3) speeds up tests by using a lower threshold.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Phase 3 tests | Unit+integration | `uv run pytest tests/test_eventbus_phase3.py -v` | all pass |
| DLQ atomic write | Manual | create tmp file, kill process mid-write, check DB state | DB row unchanged |
| Lint | Static | `uv run ruff check scripts/eventbus/` | 0 errors |
| Type check | Static | `uv run mypy scripts/eventbus/` | no new errors |
| Architecture | Static | `uv run lint-imports` | 0 violations |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** DLQ loop accesses `_db` (module global) from an asyncio task while `/publish`
  also writes to `_db` from a request handler — potential SQLite "database is locked".
  **Mitigation:** SQLite WAL mode allows one writer at a time; asyncio is single-threaded,
  so `_dlq_loop` and request handlers cannot run simultaneously — no actual concurrency.
- **Risk:** `requeue` sets `dlq_at=NULL` but the `deadletter/` file still exists — operators
  may be confused by stale files.
  **Mitigation:** Document in ops guide: deadletter files are historical artifacts; `dlq_at=NULL`
  is the authoritative signal; files may be cleaned up manually after investigation.
- **Risk:** DLQ loop interval is hardcoded to `_DLQ_INTERVAL = 60.0` s — not from config.
  **Mitigation:** Move to config in a follow-up; for Phase 3 it is acceptable as a constant.
