## Goal

Update `tests/eventbus/test_eventbus_dlq.py` to cover the new DLQ-file-write-failure counter
and the reconciliation path for missing/orphan/corrupt DLQ files (REQ-002, REQ-006;
Acceptance 4, 5).

## Scope

- Modify only `tests/eventbus/test_eventbus_dlq.py`.

## Assumptions

- `_shared_promote()` (dlq.py) calls `_atomic_write()` then sets `dlq_at`; a write failure
  should increment the new counter and leave the row unpromoted.
- The reconciliation procedure is documented in `docs/24_eventbus/eventbus_03_dlq_operations.md`
  (seq 14); this test exercises the deterministic reconciliation for missing/orphan/corrupt
  files.
- `eventbus_dlq_file_write_failure_total` is introduced by an earlier-seq procedure in this
  Plan (`scripts/eventbus/dlq.py`, seq 05); it exists by the time this test runs. (case-2
  cross-reference)

## Design decisions

- **Write-failure counter.** Fault-inject a disk-full / permission failure in `_atomic_write`
  and assert the new `eventbus_dlq_file_write_failure_total` counter increments and the DB row
  is not promoted (REQ-002; Acceptance 5).
- **Reconciliation.** Drive missing (file deleted after promotion), orphan (`dlq_at IS NULL`
  with an existing file) and corrupt (unparseable JSON) cases through the reconciliation entry
  point/procedure and assert deterministic resolution (REQ-006; Acceptance 4).

## Alternatives considered

- Testing reconciliation only via the CLI: adopt if UNK-04 selects a CLI; if a documented
  procedure is chosen, exercise it directly.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Add a fault-injection test: make `_atomic_write` raise `OSError` and assert the new counter
   increments and no `dlq_at` row is written.
2. Add reconciliation tests for orphan files (`dlq_at IS NULL` with an existing `.json`),
   missing files (`.json` absent for a promoted event) and corrupt files (unparseable JSON),
   asserting deterministic resolution per the procedure in seq 14.

### Method

Add new test functions; preserve existing DLQ tests (lines 49-330).

## Compatibility considerations

- Test-only change; no runtime impact.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py` — write-failure counter increments;
  reconciliation deterministic for missing/orphan/corrupt files.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- The test covers the write-failure counter and deterministic reconciliation of
  missing/orphan/corrupt DLQ files.

## Out of Scope

- The reconciliation implementation itself (docs, seq 14).
- The write-failure counter implementation (dlq.py, seq 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Cover write-failure counter + reconciliation path | Pending | — | — | UNK-04 (tool vs procedure) gates the reconciliation exercise |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-04 (reconciliation tool vs procedure) recorded; method needed before execution | Classified non-blocking 2026-10-25 | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-006`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`
