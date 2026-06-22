# Implementation: Event Bus app.py Phase 2 — /replay, /subscribe (SSE), offset utility

## Goal

Extend `scripts/eventbus/app.py` with `GET /replay` and `GET /subscribe` (SSE) endpoints, and
add `scripts/eventbus/offsets.py` for consumer seq offset persistence. After this phase:
consumers can receive missed events on reconnect via replay and receive live events via SSE.

## Scope

**In-Scope:**
- `scripts/eventbus/app.py` — add `/replay` and `/subscribe` to the existing Phase 1 app
- `scripts/eventbus/offsets.py` — `read_offset()` / `write_offset()` utilities
- `tests/test_eventbus_phase2.py`

**Out-of-Scope:**
- DLQ logic (Phase 3)
- `/dlq` endpoint (Phase 3)
- ACK mechanism (`acked_at` update — not required for Phase 2)

## Assumptions

1. Phase 1 app.py, db.py, config.py are in place.
2. SSE uses Starlette `StreamingResponse` with `media_type="text/event-stream"` — no
   extra dependency needed.
3. Polling interval is `poll_interval_ms` from config (default 500 ms). An `asyncio.sleep`
   loop is sufficient for current single-node traffic.
4. `since_seq=0` means "from the beginning"; missing `since_seq` defaults to 0 for `/replay`
   and to the consumer's stored offset for `/subscribe`.
5. Offset files are plain text: one integer per file (`offsets/<consumer_id>`).
6. `consumer_id` in URL path is URL-safe; path traversal is guarded by `consumer_id.replace`
   to strip `/` before constructing the file path.

## Implementation

### Target files

- `scripts/eventbus/offsets.py`
- `scripts/eventbus/app.py` (add `/replay` and `/subscribe`)
- `tests/test_eventbus_phase2.py`

### Procedure

#### Step 1: `scripts/eventbus/offsets.py`

```python
from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_offset(offsets_dir: str, consumer_id: str) -> int:
    safe_id = consumer_id.replace("/", "_").replace("..", "_")
    path = Path(offsets_dir) / safe_id
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_offset(offsets_dir: str, consumer_id: str, seq: int) -> None:
    safe_id = consumer_id.replace("/", "_").replace("..", "_")
    Path(offsets_dir).mkdir(parents=True, exist_ok=True)
    path = Path(offsets_dir) / safe_id
    path.write_text(str(seq))
    logger.debug("offset written consumer=%s seq=%d", consumer_id, seq)
```

- `safe_id` substitution prevents path traversal (`../`, `/etc/passwd`).
- `read_offset` returns 0 on missing file (consumer has never connected).
- `write_offset` is a plain `write_text` — atomic at the filesystem level on Linux
  (single-page write); sufficient for offset files.

#### Step 2: `scripts/eventbus/app.py` — `/replay` endpoint

Add to `app.py`:

```python
from fastapi import Query
from fastapi.responses import StreamingResponse

@app.get("/replay")
async def replay(
    since_seq: int = Query(default=0, ge=0),
    fmt: str = Query(default="sse", alias="format"),
):
    rows = _db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at"
        " FROM events WHERE seq > ? ORDER BY seq",
        (since_seq,),
    ).fetchall()

    if fmt == "json":
        events = [_row_to_dict(r) for r in rows]
        return events

    async def _sse_gen():
        for row in rows:
            data = json.dumps(_row_to_dict(row))
            yield f"data: {data}\n\n"

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")


def _row_to_dict(row) -> dict:
    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": json.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }
```

#### Step 3: `scripts/eventbus/app.py` — `/subscribe` SSE endpoint

```python
import asyncio

@app.get("/subscribe")
async def subscribe(
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
):
    from eventbus.offsets import read_offset

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(_cfg.offsets_dir, consumer_id)

    interval = _cfg.poll_interval_ms / 1000.0

    async def _sse_gen():
        current_seq = start_seq
        try:
            while True:
                if topic:
                    placeholders = ",".join("?" for _ in topic)
                    rows = _db.execute(
                        f"SELECT seq, event_id, topic, payload, producer, published_at"
                        f" FROM events WHERE seq > ? AND topic IN ({placeholders})"
                        f" ORDER BY seq",
                        (current_seq, *topic),
                    ).fetchall()
                else:
                    rows = _db.execute(
                        "SELECT seq, event_id, topic, payload, producer, published_at"
                        " FROM events WHERE seq > ? ORDER BY seq",
                        (current_seq,),
                    ).fetchall()

                for row in rows:
                    data = json.dumps(_row_to_dict(row))
                    yield f"data: {data}\n\n"
                    current_seq = row["seq"]

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("subscribe disconnected consumer=%s seq=%d", consumer_id, current_seq)
            if consumer_id:
                from eventbus.offsets import write_offset
                write_offset(_cfg.offsets_dir, consumer_id, current_seq)

    return StreamingResponse(_sse_gen(), media_type="text/event-stream")
```

Key design decisions:
- `topic` is a list parameter — FastAPI collects multiple `?topic=a&topic=b` into a list.
- `IN (placeholders)` is built dynamically; `?` parameters prevent SQL injection.
- On `CancelledError` (client disconnect), the offset is written before exit.
- `asyncio.sleep(interval)` yields control to the event loop between polls; the connection
  is held open by the `StreamingResponse` generator.

#### Step 4: `tests/test_eventbus_phase2.py`

```python
import json, uuid, pytest
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Same fixture pattern as phase1; reused here for clarity
    from eventbus import app as eb_app
    from eventbus.config import EventBusConfig

    cfg = EventBusConfig(
        port=8015,
        db_path=str(tmp_path / "eventbus.sqlite"),
        storage_dir=str(tmp_path / "storage"),
        offsets_dir=str(tmp_path / "offsets"),
        deadletter_dir=str(tmp_path / "deadletter"),
        max_retry=3,
    )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = Path(__file__).parent.parent / "schemas" / "event_envelope.json"
    monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)

    with TestClient(eb_app.app) as c:
        yield c


def _event(topic="test.topic"):
    return {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "payload": {"x": 1},
        "producer": "p1",
        "published_at": "2026-06-22T12:00:00Z",
    }


def test_replay_returns_events_since_seq(client):
    ev1 = _event(); ev2 = _event()
    client.post("/publish", json=ev1)
    r1 = client.post("/publish", json=ev2)
    seq1 = client.post("/publish", json=ev1).json()["seq"]  # idempotent — same seq

    r = client.get(f"/replay?since_seq=0&format=json")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev1["event_id"] in ids and ev2["event_id"] in ids


def test_replay_since_seq_filters(client):
    ev1 = _event(); ev2 = _event()
    s1 = client.post("/publish", json=ev1).json()["seq"]
    s2 = client.post("/publish", json=ev2).json()["seq"]

    r = client.get(f"/replay?since_seq={s1}&format=json")
    assert r.status_code == 200
    ids = [e["event_id"] for e in r.json()]
    assert ev1["event_id"] not in ids
    assert ev2["event_id"] in ids


def test_offset_read_write(tmp_path):
    from eventbus.offsets import read_offset, write_offset
    dir_ = str(tmp_path / "offsets")
    assert read_offset(dir_, "consumer-1") == 0
    write_offset(dir_, "consumer-1", 42)
    assert read_offset(dir_, "consumer-1") == 42


def test_subscribe_receives_published_event(client):
    ev = _event("live.topic")
    client.post("/publish", json=ev)
    with client.stream("GET", "/subscribe?topic=live.topic&since_seq=0") as r:
        lines = []
        for line in r.iter_lines():
            if line.startswith("data:"):
                lines.append(json.loads(line[5:].strip()))
                break  # TestClient SSE: read first event then stop
    assert any(e["event_id"] == ev["event_id"] for e in lines)
```

### Method

- `/replay` with `format=json` returns a plain JSON array — no SSE overhead for batch clients.
- `/subscribe` SSE uses polling rather than SQLite NOTIFY (not supported) or inotify (Linux
  only). The `poll_interval_ms` config key allows tuning without code change.
- `TestClient.stream()` reads SSE synchronously in a `with` block; the generator loop breaks
  after the first `data:` line to avoid hanging in tests.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Phase 2 tests | Unit+integration | `uv run pytest tests/test_eventbus_phase2.py -v` | all pass |
| Lint | Static | `uv run ruff check scripts/eventbus/` | 0 errors |
| Type check | Static | `uv run mypy scripts/eventbus/` | no new errors |
| Architecture | Static | `uv run lint-imports` | 0 violations |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** SQL injection via `topic` list — dynamically built `IN (?,?)`.
  **Mitigation:** placeholders are `?` symbols; actual topic values are passed as tuple
  parameters; never interpolated as strings.
- **Risk:** SSE generator holds a DB read lock during `fetchall()` while event loop is
  suspended in `asyncio.sleep()`. Other requests' reads are unblocked by WAL mode.
  **Mitigation:** WAL allows concurrent readers; only writes (`/publish`) need the write lock.
- **Risk:** `TestClient.stream()` may hang if the SSE generator never yields.
  **Mitigation:** In tests, events are pre-published before the subscribe call, so the first
  poll immediately finds rows and yields; break after first data line.
