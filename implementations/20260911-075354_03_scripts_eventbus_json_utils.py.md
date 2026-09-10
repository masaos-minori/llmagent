## Goal

Verify `OPT_SORT_KEYS` usage for canonical JSON comparison; confirm key order stability.

## Scope

Read-only verification of `scripts/eventbus/json_utils.py`:
- Verify `OPT_SORT_KEYS` is used consistently across all `dumps()` calls (REQ-001; `scripts/eventbus/json_utils.py`).
- Confirm key order stability for duplicate detection (REQ-001; `scripts/eventbus/json_utils.py`).

## Assumptions

- The canonical equality fields should include: `topic`, `payload` (canonical JSON), `producer`, `published_at`. These are the fields that determine whether two events are truly the same.
- Content comparison should use canonical JSON comparison (via `orjson.dumps()` with `OPT_SORT_KEYS`) rather than raw string comparison, to handle key ordering differences.
- Concurrent duplicate publishes are handled deterministically by SQLite's serialization via `run_with_db_lock` — the second call observes the first call's committed state.

## Design decisions

1. **Canonical equality fields (REQ-001)**: Define the following canonical equality fields:
   - `topic`: Must match exactly.
   - `payload`: Must match after canonical JSON serialization (`orjson.dumps()` with `OPT_SORT_KEYS`).
   - `producer`: Must match exactly.
   - `published_at`: Exclude from canonical equality — this field is typically generated server-side and may differ between retries.

2. **Content comparison logic (REQ-001)**: When `insert_event()` detects a duplicate (`cur.rowcount == 0`):
   - Fetch the existing row from SQLite.
   - Compare canonical fields using canonical JSON comparison.
   - Return `(seq, inserted=False, status="duplicate")` for identical content.
   - Return `(None, inserted=False, status="conflict")` for conflicting content.

3. **HTTP 409 response (REQ-003)**: In `publish_route.py`, convert `"conflict"` status to HTTP 409 with a specific error message:
   - Use the existing `ERR_EVENT_NOT_FOUND` / `ERR_EVENT_NOT_IN_DLQ` pattern for consistency.
   - Include a clear reason string (e.g., `"event already exists with different content"`).

4. **JSONL append behavior (REQ-004, REQ-005)**: Move JSONL append inside `if inserted:` block. This makes `events.jsonl` behave as a "replica" — one line per unique event, not per attempt.

5. **Documentation update (REQ-004)**: Document `events.jsonl`'s declared role in `06_eventbus_03` as a "replica" — one line per unique event, matching SQLite's deduplication semantics.

6. **ADR-006 alignment (REQ-002, REQ-003)**: Update ADR-006's Known Deviations section to note which invariants are now enforced:
   - INV-07 (at-least-once delivery): Now enforced — duplicate events cannot corrupt stored data.
   - INV-12 (ACK failure handling): Not affected by this change.
   - INV-13 (DLQ promotion priority): Not affected by this change.

## Alternatives considered

- Returning a tuple `(failure_count, status)` instead of `-2`: would break existing callers that expect an `int`.
- Using a sentinel object like `INVALID_TRANSITION = object()`: would require type annotation changes throughout the module.
- Adding a new exception class: would be overkill for a simple control-flow signal; `-2` follows the existing `-1` convention.

## Implementation
### Target file
`scripts/eventbus/json_utils.py`

### Procedure
1. Phase 1: Preparation — Declare JSONL role and document
2. Phase 2: Core Logic — Add content comparison to db.py
3. Phase 3: Core Logic — Update route layer for 409
4. Phase 4: Test updates
5. Phase 5: Documentation update
6. Phase 6: Validation

### Method
#### Phase 1: Preparation
- [ ] Document `events.jsonl`'s declared role in `06_eventbus_03` (REQ-004; `docs/06_eventbus_03_persistence_schema_and_replay.md`)
- [ ] Add idempotency contract subsection to `06_eventbus_03` (REQ-005; `docs/06_eventbus_03_persistence_schema_and_replay.md`)

#### Phase 2: Core Logic
- [ ] Add canonical equality fields definition to `db.py` (REQ-001; `scripts/eventbus/db.py`)
- [ ] Add content comparison logic to `insert_event()` when duplicate detected (REQ-001; `scripts/eventbus/db.py`)
- [ ] Update `insert_event()` return value: add `status` field for duplicate/conflict detection (REQ-002, REQ-003; `scripts/eventbus/db.py`)
- [ ] Add docstring update to `insert_event()` documenting the new return value semantics (REQ-002, REQ-003; `scripts/eventbus/db.py`)

#### Phase 3: Core Logic
- [ ] Add `ERR_EVENT_CONFLICT` constant to `route_helpers.py` (REQ-003; `scripts/eventbus/route_helpers.py`)
- [ ] Update `publish()` in `publish_route.py` to check for `"conflict"` status and raise HTTP 409 (REQ-003; `scripts/eventbus/publish_route.py`)
- [ ] Move JSONL write inside `if inserted:` block (REQ-005; `scripts/eventbus/publish_route.py`)
- [ ] Update response for 409 case with specific error message (REQ-003; `scripts/eventbus/publish_route.py`)

#### Phase 4: Test updates
- [ ] Add identical-content retry test: verify 200 returned with same seq (REQ-002; `tests/eventbus/test_eventbus_publish.py`)
- [ ] Add conflicting-content retry test: verify 409 returned (REQ-003; `tests/eventbus/test_eventbus_publish.py`)
- [ ] Add reordered-key equality test: verify identical payloads with different key order are equal (REQ-001; `tests/eventbus/test_eventbus_publish_contract.py`)
- [ ] Add JSONL reconciliation test: verify SQLite row count matches expected JSONL line count (REQ-004; `tests/eventbus/test_eventbus_publish.py`)

#### Phase 5: Documentation update
- [ ] Update ADR-006 Known Deviations section (REQ-002, REQ-003; `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`)

#### Phase 6: Validation
- [ ] Run `uv run pytest tests/eventbus/test_eventbus_publish.py -v` — publish tests pass
- [ ] Run `uv run pytest tests/eventbus/test_eventbus_publish_contract.py -v` — contract tests pass
- [ ] Run `uv run ruff format scripts/eventbus/db.py scripts/eventbus/publish_route.py && uv run ruff check scripts/eventbus/db.py scripts/eventbus/publish_route.py --fix` — lint clean
- [ ] Run `uv run mypy scripts/eventbus/db.py scripts/eventbus/publish_route.py` — type check passes

### Details

**Phase 1: Preparation**

Document `events.jsonl`'s declared role in `06_eventbus_03`. Add idempotency contract subsection to `06_eventbus_03`.

**Phase 2: Core Logic**

Extend `insert_event()` with the following logic:

```python
def insert_event(
    conn: sqlite3.Connection,
    event_id: str,
    topic: str,
    payload_str: str,
    producer: str,
    published_at: str,
) -> tuple[int | None, bool, str]:
    """INSERT OR IGNORE. Returns (seq, inserted, status).
    
    For duplicates:
      - status="duplicate": identical content, return original seq
      - status="conflict": conflicting content, return None
    
    Canonical equality fields: topic, payload (canonical JSON), producer.
    published_at is excluded from canonical equality (server-generated).
    """
    cur = conn.execute(
        "INSERT OR IGNORE INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, payload_str, producer, published_at),
    )
    conn.commit()
    inserted = cur.rowcount > 0
    
    if inserted:
        seq = int(cur.lastrowid) if cur.lastrowid else 0
        return seq, True, "inserted"
    
    # Duplicate detected — compare canonical fields
    existing_row = conn.execute(
        "SELECT topic, payload, producer FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    
    if existing_row is None:
        # Race condition: row was deleted between INSERT and SELECT
        return None, False, "conflict"
    
    # Compare canonical fields
    existing_payload_canonical = json_utils.dumps(json.loads(existing_row["payload"]))
    incoming_payload_canonical = json_utils.dumps(json.loads(payload_str))
    
    if (existing_row["topic"] == topic and 
        existing_payload_canonical == incoming_payload_canonical and
        existing_row["producer"] == producer):
        # Identical content — idempotent success
        seq = get_seq(conn, event_id)
        return seq, False, "duplicate"
    else:
        # Conflicting content — reject without modifying stored data
        return None, False, "conflict"
```

**Phase 3: Core Logic — Update route layer for 409**

Update `publish_route.py` to handle the new return value:

```python
seq, inserted, status = await run_with_db_lock(_insert)

# Handle conflict before JSONL append
if status == "conflict":
    raise HTTPException(status_code=409, detail=ERR_EVENT_CONFLICT)

# Only append JSONL for newly inserted events
if inserted:
    try:
        cfg = get_config(request)
        path = Path(cfg.storage_dir) / "events.jsonl"
        line = json_dumps({**body, "seq": seq}) + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except OSError as exc:
        logger.warning("eventbus: JSONL append failed (event still committed): %s", exc)

if inserted:
    event_dict = {
        "seq": seq,
        "event_id": event_id,
        "topic": topic,
        "payload": body["payload"],
        "producer": producer,
        "published_at": published_at,
    }
    try:
        n = broker.publish(event_dict)
        logger.debug("publish notify broker delivered=%d seq=%d", n, seq)
    except Exception:
        logger.exception("publish broker notify error seq=%d", seq)

logger.info("publish event_id=%s topic=%s seq=%d", event_id, topic, seq)
return {"event_id": event_id, "seq": seq}
```

**Phase 4: Test updates**

Add the following tests:

```python
# tests/eventbus/test_eventbus_publish.py

def test_identical_content_retry_returns_same_seq(client, eventbus_db):
    """Identical retries return the existing sequence and do not cause redelivery."""
    resp1 = client.post("/publish", json={
        "event_id": "dup-001",
        "topic": "test",
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:00Z",
    })
    assert resp1.status_code == 200
    seq1 = resp1.json()["seq"]
    
    resp2 = client.post("/publish", json={
        "event_id": "dup-001",
        "topic": "test",
        "payload": {"key": "value"},
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:01Z",  # Different timestamp
    })
    assert resp2.status_code == 200
    seq2 = resp2.json()["seq"]
    
    assert seq1 == seq2  # Same seq returned

def test_conflicting_content_retry_returns_409(client, eventbus_db):
    """Conflicting retries return HTTP 409 and do not modify the stored row."""
    resp1 = client.post("/publish", json={
        "event_id": "dup-002",
        "topic": "test",
        "payload": {"key": "value1"},
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:00Z",
    })
    assert resp1.status_code == 200
    
    resp2 = client.post("/publish", json={
        "event_id": "dup-002",
        "topic": "test",
        "payload": {"key": "value2"},  # Different payload
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:00Z",
    })
    assert resp2.status_code == 409

def test_reordered_key_equality(client, eventbus_db):
    """Reordered JSON object keys in the payload do not create a false conflict."""
    resp1 = client.post("/publish", json={
        "event_id": "dup-003",
        "topic": "test",
        "payload": {"b": 2, "a": 1},  # Keys in one order
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:00Z",
    })
    assert resp1.status_code == 200
    
    resp2 = client.post("/publish", json={
        "event_id": "dup-003",
        "topic": "test",
        "payload": {"a": 1, "b": 2},  # Keys in reverse order
        "producer": "test-producer",
        "published_at": "2024-01-01T00:00:00Z",
    })
    assert resp2.status_code == 200  # Should be 200, not 409
```

**Phase 5: Documentation update**

Update ADR-006's Known Deviations section to note which invariants are now enforced:
- INV-07 (at-least-once delivery): Now enforced — duplicate events cannot corrupt stored data.
- INV-12 (ACK failure handling): Not affected by this change.
- INV-13 (DLQ promotion priority): Not affected by this change.

## Compatibility considerations

- Changing `EventBroker.__init__` signature breaks any external callers beyond `app.py`. Verify all call sites before merging; `EventBroker` is an internal class (no public API contract), but confirm no third-party code imports it directly.
- Existing TOML configs that lack the new threshold fields will use defaults (backward compatible).
- No changes needed to callers — `EventBusConfig` construction remains the same.

## Security considerations

- The validation rules prevent misconfiguration that could hide operational issues (e.g., slow-consumer threshold above queue capacity would make health check unreachable).
- Invalid combinations fail startup with actionable errors rather than silently producing misleading health status.

## Rollback considerations

- Reverting the threshold fields requires reverting the validation logic and `load_config()` updates simultaneously.
- If reverted during runtime, the dataclass defaults ensure behavior reverts to original hardcoded values.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All docs | Quality check | `uv run python tools/check_docs_quality.py` | Clean |
| All docs | Structure check | `uv run python tools/check_docs_structure.py` | Clean |
| All docs | Consistency check | `uv run python tools/check_docs_consistency.py --domain eventbus` | Clean (if domain option exists) |
| All docs | Manual review | Human inspection | No unresolved contradictions |

## Completion criteria

- Each operation has documented preconditions, postconditions, and error responses — REQ-002
- The specification identifies the canonical source for schema, API contract, and runtime behavior — REQ-001
- The recovery runbook is executable by an operator and includes verification and rollback steps (not only detection, unlike the current `06_eventbus_03` section) — REQ-004
- Documentation checks report no unresolved contradiction introduced or left by this work — REQ-005

## Out of scope

- Deriving threshold values from load-test measurement (EB-M05).
- Backpressure disconnect behavior itself (EB-H02).
- Changing the DLQ sweep interval (`_DLQ_INTERVAL = 60.0` in `app.py`).
- Updating broker.py, health_route.py, or documentation (covered by other implementation procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read all documents and identify contradictions | Pending | — | — | |
| 2 | Map each invariant in ADR-006 to existing tests or identify gaps | Pending | — | — | |
| 3 | Map each invariant in ADR-008 to existing tests or identify gaps | Pending | — | — | |
| 4 | Add consumer identity section to 06_eventbus_04 | Pending | — | — | |
| 5 | Add ordering section to 06_eventbus_04 | Pending | — | — | |
| 6 | Add ACK/NACK rules section to 06_eventbus_04 | Pending | — | — | |
| 7 | Add offset semantics section to 06_eventbus_04 | Pending | — | — | |
| 8 | Add replay section to 06_eventbus_04 | Pending | — | — | |
| 9 | Add backpressure section to 06_eventbus_04 | Pending | — | — | |
| 10 | Add DLQ promotion/requeue section to 06_eventbus_04 | Pending | — | — | |
| 11 | Add retention section to 06_eventbus_04 | Pending | — | — | |
| 12 | Convert recovery procedure to executable runbook | Pending | — | — | |
| 13 | Correct contradictions in related documents | Pending | — | — | |
| 14 | Update cross-references in related documents | Pending | — | — | |
| 15 | Identify Known Deviations in ADRs | Pending | — | — | |
| 16 | Run documentation quality checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
