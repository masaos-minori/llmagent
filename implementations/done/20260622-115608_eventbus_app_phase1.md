# Implementation: Event Bus app.py Phase 1 — /health and /publish

## Goal

Implement `scripts/eventbus/app.py` with `GET /health` and `POST /publish` endpoints plus
`tests/test_eventbus_phase1.py`. After this phase: events can be published to SQLite and
the JSONL log, idempotency is enforced at the DB layer, and all Phase 1 tests pass.

## Scope

**In-Scope:**
- `scripts/eventbus/app.py` — FastAPI app with `/health`, `/publish`
- `scripts/eventbus/db.py` — SQLite connection helper (WAL, schema init, INSERT OR IGNORE)
- `scripts/eventbus/config.py` — TOML config loader (returns typed dataclass)
- `tests/test_eventbus_phase1.py` — unit + integration tests using `TestClient`

**Out-of-Scope:**
- `/subscribe`, `/replay`, `/dlq` endpoints (Phase 2 and 3)
- DLQ background task (Phase 3)
- offset file persistence (Phase 2)

## Assumptions

1. `config/eventbus.toml` exists (created in eventbus_infra step).
2. `schemas/event_envelope.json` exists and is valid JSON Schema draft-07.
3. Tests use a temporary SQLite DB and a temporary `storage/` directory (pytest `tmp_path`).
4. `jsonschema` is available in the project venv (it is already a transitive dependency).
5. `tomllib` is available (Python 3.11+); no `tomli` backport needed.
6. App config is loaded once at startup via FastAPI `lifespan`; not reloaded per request.

## Implementation

### Target files

- `scripts/eventbus/config.py`
- `scripts/eventbus/db.py`
- `scripts/eventbus/app.py`
- `tests/test_eventbus_phase1.py`

### Procedure

#### Step 1: `scripts/eventbus/config.py`

```python
from __future__ import annotations
import tomllib
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path("/opt/llm/config/eventbus.toml")


@dataclass(frozen=True)
class EventBusConfig:
    port: int
    db_path: str
    storage_dir: str
    offsets_dir: str
    deadletter_dir: str
    max_retry: int
    poll_interval_ms: int = 500


def load_config(path: Path | None = None) -> EventBusConfig:
    p = path or _DEFAULT_CONFIG_PATH
    with p.open("rb") as f:
        data = tomllib.load(f)
    return EventBusConfig(
        port=data["port"],
        db_path=data["db_path"],
        storage_dir=data["storage_dir"],
        offsets_dir=data["offsets_dir"],
        deadletter_dir=data["deadletter_dir"],
        max_retry=data["max_retry"],
        poll_interval_ms=data.get("poll_interval_ms", 500),
    )
```

- `frozen=True` — config is immutable after startup.
- `path` parameter enables test override without environment variable patching.

#### Step 2: `scripts/eventbus/db.py`

```python
from __future__ import annotations
import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def open_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    sql = _SCHEMA_PATH.read_text()
    conn.executescript(sql)
```

- `check_same_thread=False` — FastAPI runs handlers in a thread pool; the connection is
  protected by the GIL for single-writer use.
- `row_factory = sqlite3.Row` — allows column access by name in query results.
- `executescript` runs the full `schema.sql`; `CREATE TABLE IF NOT EXISTS` is idempotent.

#### Step 3: `scripts/eventbus/app.py`

```python
from __future__ import annotations
import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

import jsonschema
from fastapi import FastAPI, HTTPException, Request

from eventbus.config import EventBusConfig, load_config
from eventbus.db import open_db

logger = logging.getLogger(__name__)

_ENVELOPE_SCHEMA_PATH = Path("/opt/llm/schemas/event_envelope.json")
_cfg: EventBusConfig | None = None
_db: sqlite3.Connection | None = None
_envelope_schema: dict | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cfg, _db, _envelope_schema
    _cfg = load_config()
    _db = open_db(_cfg.db_path)
    _envelope_schema = json.loads(_ENVELOPE_SCHEMA_PATH.read_text())
    Path(_cfg.storage_dir).mkdir(parents=True, exist_ok=True)
    yield
    if _db:
        _db.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/publish")
async def publish(request: Request):
    body = await request.json()
    try:
        jsonschema.validate(body, _envelope_schema)
    except jsonschema.ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

    event_id = body["event_id"]
    topic = body["topic"]
    payload_str = json.dumps(body["payload"])
    producer = body["producer"]
    published_at = body["published_at"]

    cur = _db.execute(
        "INSERT OR IGNORE INTO events"
        " (event_id, topic, payload, producer, published_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, payload_str, producer, published_at),
    )
    _db.commit()

    seq = cur.lastrowid if cur.rowcount > 0 else _get_seq(event_id)

    _append_jsonl(body, seq)
    logger.info("publish event_id=%s topic=%s seq=%d", event_id, topic, seq)
    return {"event_id": event_id, "seq": seq}


def _get_seq(event_id: str) -> int:
    row = _db.execute(
        "SELECT seq FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return row["seq"] if row else 0


def _append_jsonl(body: dict, seq: int) -> None:
    path = Path(_cfg.storage_dir) / "events.jsonl"
    line = json.dumps({**body, "seq": seq}) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
```

Key design decisions:
- `INSERT OR IGNORE` — DB UNIQUE constraint on `event_id` is the idempotency gate; application
  layer just reads back the existing seq if `rowcount == 0`.
- `os.fsync` after JSONL write — ensures the line survives a process crash before OS flush.
- `lifespan` — resources opened once at startup, closed on shutdown; no per-request overhead.
- `_envelope_schema_path` is configurable via test fixtures by patching the module-level path.

#### Step 4: `tests/test_eventbus_phase1.py`

Test setup: inject a temporary config via monkeypatching `eventbus.app.load_config` and
`eventbus.app._ENVELOPE_SCHEMA_PATH`.

```python
import json
import uuid
import pytest
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
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2026-06-22T11:56:00Z",
    }


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_publish_inserts_event(client, tmp_path):
    ev = _event()
    r = client.post("/publish", json=ev)
    assert r.status_code == 200
    body = r.json()
    assert body["event_id"] == ev["event_id"]
    assert body["seq"] >= 1
    jsonl = (tmp_path / "storage" / "events.jsonl").read_text()
    assert ev["event_id"] in jsonl


def test_publish_idempotent(client):
    ev = _event()
    r1 = client.post("/publish", json=ev)
    r2 = client.post("/publish", json=ev)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["seq"] == r2.json()["seq"]


def test_publish_invalid_schema(client):
    r = client.post("/publish", json={"invalid": "body"})
    assert r.status_code == 422
```

### Method

- `TestClient` from `starlette.testclient` runs the full ASGI app synchronously — no running
  event loop needed, no subprocess.
- Config injection via `monkeypatch.setattr` replaces `load_config` before lifespan runs;
  no environment variables or config files needed in the test environment.
- JSONL existence check in `test_publish_inserts_event` verifies the atomic append path.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Phase 1 tests | Unit+integration | `uv run pytest tests/test_eventbus_phase1.py -v` | all pass |
| Lint | Static | `uv run ruff check scripts/eventbus/` | 0 errors |
| Type check | Static | `uv run mypy scripts/eventbus/` | no new errors |
| Architecture | Static | `uv run lint-imports` | 0 violations |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** `check_same_thread=False` on SQLite connection is safe for single-writer
  (`/publish`) but unsafe if multiple threads write concurrently.
  **Mitigation:** Phase 1 has one writer endpoint; Phase 3 DLQ task runs in the same
  thread via asyncio. If true concurrency is needed, switch to `aiosqlite`.
- **Risk:** `_cfg`, `_db`, `_envelope_schema` are module-level globals — test isolation
  depends on `TestClient` triggering `lifespan` correctly.
  **Mitigation:** `with TestClient(app)` enters/exits lifespan on `__enter__`/`__exit__`;
  each test fixture creates a new client with fresh tmp_path.
