## Goal

Add one idempotent reconciliation function `reconcile_missing_dlq_files()` to
`scripts/eventbus/dlq.py` that detects dead-letter rows (`events.dlq_at IS NOT
NULL`) whose `{event_id}.json` file is missing and rebuilds each file from SQLite
through the existing `_atomic_write` path, returning operator-readable counts
(checked, rebuilt, failed) (REQ-001, REQ-002, REQ-003).

## Scope

- In-scope: add `reconcile_missing_dlq_files(db, deadletter_dir) -> dict` to
  `scripts/eventbus/dlq.py` beside `sweep_orphans`. It selects promoted rows whose
  file is absent, rebuilds each via `_atomic_write`, and returns a plain dict of
  ints. No change to any existing function, route, or caller signature.
- Out-of-scope: the operator entry point (a `tools/` script, an operator-role
  route, or a startup check) — `REQ-005` / `UNK-01` is an open owner decision with
  no frozen row; this procedure implements only the library function and leaves the
  return dict for a future entry point to render. Backfilling the JSONL archive,
  changes to promotion (`_shared_promote`), requeue, or the NACK route, and backup/
  restore of `eventbus.sqlite` are out of scope.

## Assumptions

- The rebuilt file is byte-equivalent in content to a fresh promotion of the same
  event **except** for `dlq_at`, which comes from the stored row value rather than a
  new timestamp. `_build_dlq_record` forces `dlq_at=now`, so this procedure builds
  the `DlqEventRecord` directly from the row fields instead of calling
  `_build_dlq_record`.
- `checked` counts rows with `dlq_at IS NOT NULL` whose file is looked up,
  **excluding** archived requeued originals (their file was moved to
  `{deadletter_dir}/requeued/` and a descendant row with `redelivered_from` was
  created). The query population therefore mirrors what `fetch_dlq` lists: live
  DLQ rows only. This resolves design note `UNK-03` to "exclude requeued
  originals".
- The function is lock-free like `sweep_orphans`: it takes a raw
  `sqlite3.Connection` and does **not** acquire `run_with_db_lock` itself. The
  caller wraps the call in `run_with_db_lock` (as `_dlq_loop` does for the sweep),
  which is what makes it safe beside inline `/nack` promotion and the sweep loop.
  `UNK-02` (report-only vs also-rebuild for a startup check) affects only a future
  entry point, not this function.

## Design decisions

- Placement beside `sweep_orphans` in `dlq.py`, not `dlq_repo.py`: the module
  already owns both the DLQ file writes and its SQLite queries (`_shared_promote`
  reads `events`/`consumer_delivery` directly); a cross-module hop adds no benefit.
  `dlq_repo.py` stays a reference file.
- Return a plain `dict` of ints (`checked`, `rebuilt`, `failed`) so any future entry
  point (script, route, startup check) can render it without coupling to this
  module — phase-gated by `UNK-01`.
- Idempotence by construction: the file-exists check gates the write, so an existing
  file is never rewritten or deleted; a second run reports the same `checked` count
  and `rebuilt = 0`.

## Alternatives considered

- Building the record through `_build_dlq_record(row, now_iso(), ...)`: rejected —
  it pins `dlq_at` to "now", which would corrupt the audit trail for a file lost
  after the original promotion. The row's stored `dlq_at` must be preserved.
- Querying `dlq_repo.py` for the rows: rejected — `_shared_promote` already reads
  `events`/`consumer_delivery` directly from `dlq.py`, and splitting the read would
  add a cross-module hop with no benefit.

## Implementation

### Target file

`scripts/eventbus/dlq.py` (exists; not a new file).

### Procedure

1. Add `reconcile_missing_dlq_files(db, deadletter_dir)` to
   `scripts/eventbus/dlq.py`, placed immediately after `sweep_orphans`
   (around line 190) so it sits beside the sweep it complements.
2. Select promoted rows whose file is absent, rebuild each via `_atomic_write`, and
   return `{checked, rebuilt, failed}`.
3. Leave every existing symbol, signature, and caller untouched.

### Method

```python
def reconcile_missing_dlq_files(
    db: sqlite3.Connection,
    deadletter_dir: str,
) -> dict[str, int]:
    """Detect and rebuild DLQ files lost after promotion.

    REQ-001, REQ-002, REQ-003: lists promoted events (dlq_at IS NOT NULL) whose
    {event_id}.json file is absent and rebuilds each through _atomic_write, reusing
    the sweep's failure metering. Lock-free by design (see Assumptions): the caller
    holds run_with_db_lock, exactly as it does for sweep_orphans. Idempotent — an
    existing file is never rewritten. Returns {checked, rebuilt, failed}.
    """
    checked = rebuilt = failed = 0
    rows = db.execute(
        "SELECT e.seq, e.event_id, e.topic, e.payload, e.producer,"  # nosec B608 — constant SQL fragment, values parameterized
        " e.published_at, e.dlq_at"
        " FROM events e"
        " WHERE e.dlq_at IS NOT NULL"
        " AND NOT EXISTS (SELECT 1 FROM events d WHERE d.redelivered_from = e.event_id)"
    ).fetchall()

    for row in rows:
        checked += 1
        event_id = row["event_id"]
        dst = Path(deadletter_dir) / f"{event_id}.json"
        if dst.exists():
            continue
        consumer_row = db.execute(
            f"SELECT MAX({_COL_CONSUMER_DELIVERY_FAILURE_COUNT}) FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
            "WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        failure_count = (
            int(consumer_row[0]) if consumer_row and consumer_row[0] else None
        )
        record = DlqEventRecord(
            seq=row["seq"],
            event_id=event_id,
            topic=row["topic"],
            payload=orjson.loads(row["payload"]),
            producer=row["producer"],
            published_at=row["published_at"],
            dlq_at=row["dlq_at"],
            consumer_delivery_failure_count=failure_count,
        )
        try:
            _atomic_write(deadletter_dir, event_id, record)
        except OSError:
            _dlq_file_write_failure_counter.inc()
            logger.exception(
                "dlq reconcile: DLQ file write failed event_id=%s", event_id
            )
            failed += 1
            continue
        rebuilt += 1

    return {"checked": checked, "rebuilt": rebuilt, "failed": failed}
```

Notes on the method:

- The `NOT EXISTS (redelivered_from = event_id)` clause excludes requeued originals
  (resolves `UNK-03`); it keeps `checked` aligned with what `fetch_dlq` lists.
- `dlq_at=row["dlq_at"]` preserves the stored timestamp; the record is built
  directly, bypassing `_build_dlq_record` (which would force `now_iso()`).
- The per-event `MAX(consumer_delivery_failure_count)` lookup mirrors
  `_shared_promote` (line 107).
- Failure metering reuses `_dlq_file_write_failure_counter` and `continue`s on
  `OSError`, exactly as `_shared_promote` (lines 116-121) does, so one failing
  event does not stop the rest (AC-4).
- `Path` is already imported at the top of the module (used by `_atomic_write` and
  `archive_dlq_record`); no new import is required.

### Details

- REQ-001 content contract: the rebuilt file carries `seq`, `event_id`, `topic`,
  `payload`, `producer`, `published_at`, the stored `dlq_at` and the max
  per-consumer failure count — identical to a fresh promotion except `dlq_at`.
  `_atomic_write` serializes the record with `orjson.dumps(record)` (line 222), so
  byte-equivalence follows from constructing the same `DlqEventRecord` shape.
- AC-3 (a row without `dlq_at` is never turned into a file) holds because the query
  filters `dlq_at IS NOT NULL`; the sweep owns the `dlq_at IS NULL` promotion path.
- Idempotence (AC-2): `dst.exists()` short-circuits before any write, so an
  unchanged directory yields `rebuilt = 0` on a second run.

## Compatibility considerations

- No public contract changes: the function is new, takes a raw connection and a
  directory string, and returns a plain dict. No existing route, caller, or
  signature is touched.
- The sweep path (`sweep_orphans` → `_shared_promote`) is unchanged; this function
  is a sibling, not a refactor.

## Security considerations

- Parameterized SQL throughout (values bound via tuples; column/index names are
  module-level constants or fixed identifiers), matching the existing `nosec`
  pattern in `_shared_promote` and `is_promotable`. No user input reaches the query.
- File writes stay inside `deadletter_dir` via `Path(deadletter_dir) / f"{event_id}.json"`;
  `event_id` is a stored value written through `_atomic_write`'s temp-file +
  `os.replace` path, so no path traversal beyond the existing promotion path.

## Rollback considerations

- Revert the implementing commit: the change is a single added function with no
  edits to existing code, so a single logical revert restores the prior state.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/dlq.py` | Static gates | `uv run ruff check scripts/eventbus/dlq.py`, `uv run mypy scripts/eventbus/dlq.py`, `uv run radon cc scripts/eventbus/dlq.py`, `uv run vulture scripts/eventbus/dlq.py`, `uv run bandit -r scripts/eventbus/dlq.py` | New function rank A or B; file average not degraded (>30 % drop or any D/E block forbidden); no new vulture/bandit findings |
| `scripts/eventbus/dlq.py` | Behaviour (via sibling test procedure) | `uv run pytest tests/eventbus/test_eventbus_dlq.py` | Reconcile regression + concurrency tests pass; existing DLQ tests unchanged |

## Completion criteria

- `reconcile_missing_dlq_files(db, deadletter_dir)` exists in
  `scripts/eventbus/dlq.py` and returns `{checked, rebuilt, failed}`.
- It considers only `dlq_at IS NOT NULL` rows and never rewrites an existing file
  (AC-1, AC-2, AC-3).
- A write failure on one event is metered via `_dlq_file_write_failure_counter` and
  skipped without stopping the rest (AC-4).
- The function is lock-free; safety comes from the caller holding `run_with_db_lock`
  (AC-5, exercised by the sibling test procedure).
- `ruff`/`mypy` clean; `radon` rank A/B; no new `vulture`/`bandit` findings.

## Out of Scope

- The operator entry point and its runbook command (`REQ-005` / `UNK-01`): no row
  frozen; a future procedure implements it once the owner decides.
- Any change to `scripts/eventbus/dlq_repo.py`, the routes, the NACK route, or the
  JSONL archive.
- The tests themselves: they live in the sibling procedure
  `implementations/20261029-085348_02_tests_eventbus_test_eventbus_dlq.py.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `reconcile_missing_dlq_files()` (REQ-001, REQ-002, REQ-003) | Pending | — | — | Lock-free; caller holds run_with_db_lock |
| 2 | Apply static gates to scripts/eventbus/dlq.py (REQ-001..REQ-003) | Pending | — | — | ruff/mypy/radon/vulture/bandit |
| 3 | Run the DLQ suite with the sibling test procedure (REQ-001..REQ-003) | Pending | — | — | Tests authored in the 02 procedure |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: `issues/20261028-122233_ebdlqrecon002_rebuild-missing-dlq-files.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-085348
- **Related target files**: `scripts/eventbus/dlq.py`
