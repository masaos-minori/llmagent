## Goal

Add a characterization/guard test confirming `dlq.py::promote_single()`'s
DB-non-update-on-write-failure invariant: if `_atomic_write()` fails, the DB row is
left unchanged. No production code change.

## Scope

- In scope: add one test to `tests/eventbus/test_eventbus_dlq.py` covering
  `promote_single()`'s write-then-update ordering under `_atomic_write()` failure.
- Out of scope: the two sibling target files in the same plan
  (`tests/db/test_sqlite_helper.py`, `tests/rag/ingestion/test_chunk_splitter.py`, each
  with its own implementation procedure document); `promote_batch()` (shares the same
  pattern but is not the target of this item); any production code change.

## Assumptions

- `promote_single()` (`scripts/eventbus/dlq.py:114-144`, verified this cycle) writes
  the DLQ JSON file via `_atomic_write()` *before* updating the DB row
  (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`), matching its
  own docstring: "if `_atomic_write` fails, the DB row is not updated and the event
  remains live." Monkeypatching `_atomic_write` to raise lets the test assert this
  ordering directly.
- `_atomic_write` must be patched at `eventbus.dlq._atomic_write` (the module-local
  name `promote_single()` actually calls), not a re-exported alias — confirmed by
  reading the import/call site in `dlq.py`.
- No existing test in `tests/eventbus/test_eventbus_dlq.py` covers this failure path —
  confirmed via `grep -n "def test_" tests/eventbus/test_eventbus_dlq.py`; the file's 10
  existing tests cover DLQ promotion via retry-exhaustion, listing, requeue, and inline
  nack-triggered promotion, but none inject an `_atomic_write` failure.
- The file's established pattern for accessing the underlying DB directly alongside the
  `client` fixture is `from eventbus.db import open_db; db = open_db(str(tmp_path /
  "eventbus.sqlite"))` (used by `test_inline_dlq_promotion_on_nack` and
  `test_inline_dlq_promotion_skipped_below_threshold`); publish the event via
  `client.post("/publish", json=ev)` using the file's existing `_event()` helper, then
  call `promote_single(db, deadletter_dir, ev["event_id"])` directly.

## Design decisions

- Reuse the existing `client`/`tmp_path` fixture and `_event()` helper rather than
  introducing a new fixture, keeping this test consistent with the file's established
  style.
- Call `promote_single()` directly (not via an HTTP endpoint) so the test isolates the
  write-then-update invariant itself, independent of the `/nack` threshold-triggering
  logic already covered by `test_inline_dlq_promotion_on_nack`.

## Alternatives considered

- Driving the failure through repeated `/nack` calls until inline promotion triggers,
  then monkeypatching `_atomic_write` — rejected: calling `promote_single()` directly
  is simpler and avoids coupling this test to the nack-threshold mechanics already
  covered elsewhere.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Add `test_atomic_write_failure_leaves_db_row_unchanged(client, tmp_path,
   monkeypatch)`.
2. Publish a live event via `client.post("/publish", json=_event())`.
3. Open a direct DB connection: `from eventbus.db import open_db; db =
   open_db(str(tmp_path / "eventbus.sqlite"))`.
4. Monkeypatch `eventbus.dlq._atomic_write` to raise `OSError("disk full")`.
5. Call `promote_single(db, str(tmp_path / "deadletter"), event_id)` inside
   `pytest.raises(OSError)`.
6. Query `SELECT dlq_at FROM events WHERE event_id = ?` and assert `row["dlq_at"] is
   None` (unchanged from the live/un-promoted state).

### Method

```python
def test_atomic_write_failure_leaves_db_row_unchanged(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from eventbus import dlq
    from eventbus.db import open_db

    ev = _event()
    client.post("/publish", json=ev)
    db = open_db(str(tmp_path / "eventbus.sqlite"))

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(dlq, "_atomic_write", _raise)

    with pytest.raises(OSError):
        dlq.promote_single(db, str(tmp_path / "deadletter"), ev["event_id"])

    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (ev["event_id"],)
    ).fetchone()
    assert row["dlq_at"] is None
```

### Details

`promote_single()` (verified this cycle, `scripts/eventbus/dlq.py:114-144`):
```python
def promote_single(db, deadletter_dir, event_id) -> bool:
    """...Write the JSON file before updating the DB row to preserve consistency:
    if _atomic_write fails, the DB row is not updated and the event remains live."""
    ...
    record = _build_dlq_record(row, now)
    _atomic_write(deadletter_dir, event_id, record)
    cur = db.execute("UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL", ...)
    ...
```
The monkeypatched `_atomic_write` raises before the `UPDATE` statement executes,
directly exercising the documented invariant.

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: test-only change against a temporary, non-production SQLite file and temp
directory; no secrets, network, or external input involved.

## Rollback considerations

Delete the new test function; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_dlq.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_dlq.py -v` | New test passes, no regression in existing 10 tests |
| `tests/eventbus/` (full) | Regression | `uv run pytest tests/eventbus/ -v` | No new failures |
| `tests/eventbus/test_eventbus_dlq.py` | Static | `uv run ruff check tests/eventbus/test_eventbus_dlq.py` + `uv run mypy tests/eventbus/test_eventbus_dlq.py` | Clean |

## Out of scope

`promote_batch()`; the other 2 target files in this plan; any change to
`scripts/eventbus/dlq.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/done/20260726-125412_require.md`
- **Source plan**: `plans/20260823-194857_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-182410
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`

## Adversarial verification notes (this cycle)

- Corrected the source plan's Traceability section: `Source requirement` pointed to
  `requires/20260726-125412_require.md`, which does not exist — the file is at
  `requires/done/20260726-125412_require.md` (confirmed by file-existence check).
  Fixed in `plans/20260823-194857_plan.md` directly (shared fix across all 3
  implementation procedure documents generated from this plan).
- Re-verified `promote_single()`'s write-then-update ordering and the exact call site
  of `_atomic_write` against current source — matches the plan exactly.
- Confirmed via `grep -n "def test_" tests/eventbus/test_eventbus_dlq.py` that no
  existing test covers this failure path, and via
  `grep -rl "20260823-194857_plan" implementations/ implementations/done/` that no
  duplicate implementation procedure document exists. No other blocking unknowns or
  contradictions found for this target file (see the sibling `test_chunk_splitter.py`
  procedure document for a separate, substantive Design correction made to this same
  plan).
