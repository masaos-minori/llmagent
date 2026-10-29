## Goal

Add tests for `reconcile_missing_dlq_files (new)` (created by seq 01, `scripts/eventbus/dlq.py`). The function rebuilds a lost DLQ file for a promoted event (`dlq_at IS NOT NULL`) from the SQLite row, skips events whose `dlq_at IS NULL`, is idempotent on intact files, isolates a single event's write failure, and is safe under concurrent callers holding the DB lock.

## Scope

Append new test functions to `tests/eventbus/test_eventbus_dlq.py`. No change to production code (seq 01 owns that). No change to existing tests.

## Assumptions

- `reconcile_missing_dlq_files (new)` is created by seq 01 (`implementations/20261029-085348_01_scripts_eventbus_dlq.py.md`); it is marked `(new)` here because it does not yet exist in the repo.
- The function reads only (promoted events), builds the record inline, and writes via `dlq._atomic_write`; it catches a per-event write failure, meters it, logs it, and skips that event without blocking others.
- The real caller holds `eventbus.db.get_db_lock()` around the call (see seq 01, lock discipline). Tests mirror this by acquiring the lock per thread.
- `open_db` returns a `sqlite3.Connection(check_same_thread=False)` shared connection; concurrent OS threads must serialize through `get_db_lock()`.
- Promotion to `dlq_at IS NOT NULL` requires a `consumer_delivery` row with `consumer_delivery_failure_count >= 2` (same rule as `sweep_orphans`).
- `_event()` and the `client`/`tmp_path` fixtures already exist in this file (used by the existing tests at lines 686-753).

## Design decisions

- Append after the existing `test_reconciliation_missing_file` (line 753) so the added region sits just before the next existing block. This keeps the new tests adjacent to the orphan/missing DLQ coverage.
- Rebuild correctness is verified by byte-equality against the pre-delete bytes: the rebuilt record must equal the sweep-time record field-for-field.
- Idempotency is verified by `st_mtime_ns` preservation: an intact file must not be rewritten.
- Failure isolation is verified by monkeypatching `dlq._atomic_write` to raise `OSError` for exactly one event's payload, then asserting only the other event is reconciled.
- Concurrency is verified with two threads each holding `get_db_lock()` around its call; the shared non-reentrant lock serializes them by design (no barrier).

## Alternatives considered

- Byte-equality vs field-by-field compare: byte-equality is stricter and matches the "identical to the sweep-time record" contract; fall back to field-by-field only if the rebuild differs in a non-material field.
- Read-only-directory failure injection instead of monkeypatch: rejected (non-deterministic across environments, root bypasses perms).
- Barrier inside the lock: rejected — `get_db_lock()` is a non-reentrant `threading.Lock`, so a `Barrier(2)` inside the critical section deadlocks (only one thread can hold the lock, the other never reaches `barrier.wait()`).

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py` (append region, after line 753).

### Procedure

1. Open `tests/eventbus/test_eventbus_dlq.py` and position the cursor at the end of `test_reconciliation_missing_file` (line 753), after its final `assert`.
2. Insert a blank line, then append the five test functions below verbatim.
3. Ensure the imports inside each function match the procedure exactly.
4. Run `stale_detector.py` on this document (must pass).

### Method

Append the following block to the end of the file:

```python
# ---------------------------------------------------------------------------
# reconcile_missing_dlq_files (new) — rebuild lost DLQ files for promoted events
# ---------------------------------------------------------------------------


def test_reconcile_rebuilds_full_record_from_db(
    client: TestClient, tmp_path: Path
) -> None:
    """A promoted event whose file was lost is rebuilt byte-for-byte from SQLite."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Promote via sweep so the event has a DLQ record, then delete the file.
    _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    original_bytes = (tmp_path / "deadletter" / f"{ev['event_id']}.json").read_bytes()
    (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # Reconcile returns {checked, rebuilt, failed}; the file is absent so it rebuilds.
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    assert reconciled == {"checked": 1, "rebuilt": 1, "failed": 0}

    rebuilt = (tmp_path / "deadletter" / f"{ev['event_id']}.json").read_bytes()
    assert rebuilt == original_bytes  # byte-for-byte identical to sweep-time record
```

```python
def test_reconcile_ignores_unpromoted_events(
    client: TestClient, tmp_path: Path
) -> None:
    """Events with dlq_at IS NULL are not touched (only promoted events are reconciled)."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)
    # Never promoted: dlq_at stays NULL.
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    assert reconciled == {"checked": 0, "rebuilt": 0, "failed": 0}
    assert not (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()
```

```python
def test_reconcile_is_idempotent_and_preserves_existing_file(
    client: TestClient, tmp_path: Path
) -> None:
    """Re-running reconcile on an intact file leaves it untouched (no rewrite, mtime preserved)."""
    from eventbus.db import open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))
    ev = _event()
    client.post("/publish", json=ev)

    # Promote via sweep; do NOT delete the file, so reconcile must skip it.
    _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    target = tmp_path / "deadletter" / f"{ev['event_id']}.json"
    stat_before = target.stat()
    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    # File already present: counted as checked, but never rewritten (rebuilt == 0).
    assert reconciled == {"checked": 1, "rebuilt": 0, "failed": 0}
    stat_after = target.stat()
    assert (
        stat_before.st_mtime_ns == stat_after.st_mtime_ns
    )  # existing file not rewritten
```

```python
def test_reconcile_isolates_single_event_write_failure(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """A write failure for one event is skipped without blocking the others."""
    from eventbus import dlq
    from eventbus.db import open_db
    from eventbus.dlq import _atomic_write, reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev1 = _event()
    ev2 = _event()
    client.post("/publish", json=ev1)
    client.post("/publish", json=ev2)

    for ev in (ev1, ev2):
        _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Delete both files; both are now reconcile targets.
    for ev in (ev1, ev2):
        (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # _atomic_write is a module-level function: (deadletter_dir, event_id, record).
    # Force the write of ev1 to fail; ev2 writes normally via the real function.
    def flaky_atomic_write(deadletter_dir, event_id, record):
        if event_id == ev1["event_id"]:
            raise OSError("simulated disk failure")
        return _atomic_write(deadletter_dir, event_id, record)

    monkeypatch.setattr(dlq, "_atomic_write", flaky_atomic_write)

    reconciled = reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))
    # ev1 fails, ev2 succeeds: checked=2, rebuilt=1, failed=1.
    assert reconciled == {"checked": 2, "rebuilt": 1, "failed": 1}

    assert (tmp_path / "deadletter" / f"{ev2['event_id']}.json").exists()
    assert not (tmp_path / "deadletter" / f"{ev1['event_id']}.json").exists()

    # Both events were promoted by sweep (dlq_at set); only the file differs.
    row1 = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev1["event_id"],)
    ).fetchone()
    row2 = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev2["event_id"],)
    ).fetchone()
    assert row1["dlq_at"] is not None
    assert row2["dlq_at"] is not None

    # The single write failure was metered on the failure counter.
    assert _dlq_failure_counter() >= 1.0
```

```python
def test_reconcile_concurrent_callers_under_db_lock(
    client: TestClient, tmp_path: Path
) -> None:
    """Two callers each holding get_db_lock() reconcile their events without corruption."""
    import threading

    from eventbus.db import get_db_lock, open_db
    from eventbus.dlq import reconcile_missing_dlq_files, sweep_orphans

    db = open_db(str(tmp_path / "eventbus.sqlite"))

    ev_a = _event()
    ev_b = _event()
    client.post("/publish", json=ev_a)
    client.post("/publish", json=ev_b)

    for ev in (ev_a, ev_b):
        _make_promotable(db, ev["event_id"])
    sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

    # Delete both files; both are now reconcile targets.
    for ev in (ev_a, ev_b):
        (tmp_path / "deadletter" / f"{ev['event_id']}.json").unlink()

    # get_db_lock() is a non-reentrant threading.Lock, so two callers that both hold
    # it serialize by design. Each worker mirrors the real caller: hold the lock
    # around the whole reconcile call. No sleeps or barriers.
    def worker() -> None:
        with get_db_lock():
            reconcile_missing_dlq_files(db, str(tmp_path / "deadletter"))

    t_a = threading.Thread(target=worker)
    t_b = threading.Thread(target=worker)
    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    for ev in (ev_a, ev_b):
        assert (tmp_path / "deadletter" / f"{ev['event_id']}.json").exists()
        row = db.execute(
            "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
        ).fetchone()
        assert row["dlq_at"] is not None
```

### Details

- `reconcile_missing_dlq_files` returns a plain dict `{checked, rebuilt, failed}` (plan-mandated `-> dict`, ebdlqrecon002). Tests assert on those keys, not on a bare int.
- `_atomic_write` is a module-level function `(deadletter_dir, event_id, record)`; the failure-isolation test monkeypatches `eventbus.dlq._atomic_write` (the name `reconcile_missing_dlq_files` resolves at call time), keeping the same 3-arg signature and dispatching to the real function for the non-failing event. There is no such manager class; `_atomic_write` is module-level.
- The concurrency test holds the shared non-reentrant `get_db_lock()` per thread, so the two workers serialize by design; no `threading.Barrier` is used (a barrier inside the lock would deadlock).
- All SQL identifiers are written as string literals (not backticked in prose); they are not Python symbols.

## Compatibility considerations

- The new tests import `reconcile_missing_dlq_files (new)` and `_atomic_write` from `eventbus.dlq`; both must exist after seq 01. `_atomic_write` already exists (seq 01 references it).
- Appended region does not overlap the `ebaudit005` test region on the same file (different line ranges); ordering is sequential.

## Security considerations

None. Tests operate under `tmp_path` and a throwaway SQLite file.

## Rollback considerations

Delete the five appended functions to revert. No production code changes are made by this document.

## Validation plan

1. Run the new tests directly: `pytest tests/eventbus/test_eventbus_dlq.py -k "reconcile_" -v`.
2. Confirm all five pass: rebuild, ignore-unpromoted, idempotent/mtime, failure-isolation, concurrency.
3. Run the full DLQ test module: `pytest tests/eventbus/test_eventbus_dlq.py`.
4. Run the full suite per `rules/toolchain.md`.
5. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- Five new tests appended to `tests/eventbus/test_eventbus_dlq.py`, passing.
- `reconcile_missing_dlq_files (new)` covered by rebuild + idempotency + isolation + concurrency assertions.
- Full suite green; `stale_detector.py` clean.

## Out of Scope

- Production implementation of `reconcile_missing_dlq_files (new)` (seq 01).
- JSONL-archive rebuild path (out of scope per plan; `dlq_at IS NULL` events excluded).
- `ebaudit005` audit assertions on the same file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261029-104712 | Appended 5 corrected tests. Original proc code diverged from plan's `-> dict` contract; see Blocker Log. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261029-104712 | Deliverable; all 5 tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261029-104712 | DLQ module 25 passed; ruff check+format clean; concurrency stable x5; stale_detector clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261029-104712 | Docs out of scope for this doc. Proc doc's Method/Details corrected to match delivered code (see Blocker Log). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-2 | Proc-02 verbatim tests contradicted the plan-mandated `reconcile_missing_dlq_files -> dict` contract: asserted bare-int returns, referenced a non-existent manager class for the atomic-write monkeypatch target, monkeypatched `_atomic_write` with the wrong signature, called `sweep_orphans` unimported, and deadlocked on a `Barrier` inside the non-reentrant lock. Fixed by rewriting the 5 tests against the dict contract and module-level `_atomic_write`. | Yes | 20261029-104712 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-085348
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`
