## Goal

Add a DLQ-file-write-failure counter around `_atomic_write()` in `scripts/eventbus/dlq.py` so
the previously silent write-failure path is observable, without changing the
write-file-then-set-`dlq_at` durability boundary (REQ-002; Acceptance 5).

## Scope

- Modify only `scripts/eventbus/dlq.py`: `_shared_promote()` (current lines 81-117) and the
  module-level metric definitions.

## Assumptions

- `_shared_promote()` calls `_atomic_write(deadletter_dir, event_id, record)` (line 108) then
  sets `dlq_at` in SQLite (lines 109-113); a write failure raises `OSError` and currently
  aborts the rest of the sweep cycle (caught by `_dlq_loop`).
- The write-file-then-set-`dlq_at` order is the SQLite durability boundary (Out-of-Scope in the
  plan; H-01) and MUST NOT change.

## Design decisions

- **New counter.** Add `eventbus_dlq_file_write_failure_total` (new) as a module-level
  `Counter`, mirroring the JSONL/broker counters, and wrap the `_atomic_write()` call in
  `_shared_promote()` in a try/except that increments it on `OSError` before re-raising, so the
  durability order is unchanged and the failure is counted (REQ-002; Acceptance 5).

## Alternatives considered

- Logging the failure only: rejected — REQ-002 requires observability outside the process log.

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

1. Add a module-level `eventbus_dlq_file_write_failure_total` (new) Counter near the other
   module metrics.
2. In `_shared_promote()` (lines 81-117), wrap the `_atomic_write(...)` call (line 108) in a
   `try/except OSError` that increments the new counter and re-raises, preserving the existing
   propagation to `_dlq_loop`.
3. Do not alter the ordering of `_atomic_write` (line 108) relative to the `UPDATE events SET
   dlq_at` (line 110) and `db.commit()` (line 113).

### Method

In-place edit: add the metric definition and a try/except around the existing call. No new
module-level symbols besides the counter.

### Details

- The counter name `eventbus_dlq_file_write_failure_total` (new) must not carry any event_id,
  path, or token value (INV-05, REQ-007) — label it generically.
- Re-raise after counting so the sweep-cycle failure behavior is unchanged.

## Compatibility considerations

- New additive counter; document it in `docs/24_eventbus/eventbus_09_publish_durability.md`
  (seq 12).

## Security considerations

- The counter must not include the dead-letter path, event_id, or record contents (INV-05,
  REQ-007).

## Rollback considerations

- Revert the commit; the counter and its guard are removed.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py` — fault-inject a disk-full / permission
  failure in `_atomic_write`; assert the new counter increments and the DB row is not
  promoted.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- A write failure inside `_atomic_write` increments `eventbus_dlq_file_write_failure_total` (new)
  while leaving the write-file-then-set-`dlq_at` durability order intact.

## Out of Scope

- Changing the durability order or the sweep-cycle failure propagation.
- The reconciliation path (docs, seq 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the DLQ-file-write-failure counter around `_atomic_write` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `scripts/eventbus/dlq.py`
