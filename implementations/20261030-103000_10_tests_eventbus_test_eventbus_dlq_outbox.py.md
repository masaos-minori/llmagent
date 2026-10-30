# Implementation Procedure: test_eventbus_dlq_outbox.py crash-window suite

## Goal

Create `tests/eventbus/test_eventbus_dlq_outbox.py` (new module) covering every crash window,
retry lifecycle, isolation, and restart case of the outbox worker (REQ-004–REQ-006, REQ-009;
plan AC-3, AC-4).

## Scope

**In scope:**
- New test module exercising `process_outbox` (new) through the real app lifespan and direct worker
  calls with fault injection.

**Out of scope:**
- Promotion-transaction contracts (row 09), shutdown join (row 11).

## Assumptions
- Verified at HEAD `124e340b4`: the module does not exist (new, plan row evidence).
- Harness pattern mirrors `test_eventbus_dlq.py::client` (TestClient + tmp dirs +
  `eventbus_test_tokens`) so the loop wiring (row 06) participates.

## Design decisions
- Case list (one test each, named for the crash window):
  1. `test_commit_then_crash_before_file` (new): promote via NACK, kill nothing — pending row +
     no file; one loop cycle generates the file and marks `done` (REQ-004/AC-3 restart
     analogue in-process).
  2. `test_crash_during_tmp_write_leaves_interrupted_tmp` (new): monkeypatch `os.replace` to raise
     once mid-`_atomic_write`; leftover `.dlq_tmp_*` is reported by reconcile
     `interrupted_tmp` (new) (REQ-007 cross-check) and the outbox row records the failed attempt.
  3. `test_one_failing_artifact_does_not_block_others` (new): two promoted events, `os.replace`
     patched to fail only for event A's destination; B reaches `done`, A gains
     `attempts=1`, `last_error`, a future `next_attempt_at` (new) (REQ-005/AC-4, isolation AC-3).
  4. `test_terminal_failed_after_bound` (new): failing patch across `cfg.outbox_max_attempts`
     cycles → row `status='failed'`, terminal counter incremented, subsequent cycles skip it
     (REQ-005).
  5. `test_restart_with_pending_rows` (new): build pending rows, close the app, reopen a new
     TestClient lifespan; first cycle processes them (REQ-006/AC-3).
  6. `test_idempotent_reprocessing_no_rewrite` (new): file already present with matching content
     → re-processing marks `done` without touching the file's mtime/content (double-write
     risk mitigation).
  7. `test_failed_row_never_undoes_committed_dlq_state` (new): filesystem failures never clear
     `dlq_at` or duplicate events (REQ-009).
- Faults injected with `monkeypatch` on `os.replace` keyed by destination path; deterministic,
  no sleeps: tests call `process_outbox` (new) directly with an injected synchronous `run_locked` (new)
  runner for lifecycle cases, and use the lifespan only where the loop itself is the subject
  (cases 5/6).

## Alternatives considered
- Subprocess crash tests: rejected — monkeypatched crash points give the same coverage
  deterministically; the plan's crash windows are commit-boundary windows, not power loss.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_outbox.py` (new)

### Procedure
1. Create the module with the shared harness import (`tests.eventbus.eventbus_helpers`).
2. Implement the seven cases above.

### Method
Fixtures create promoted state through the NACK endpoint where practical (real gating),
direct `promote_single` where gating is irrelevant.

### Details
- Assert persisted values (`attempts`, `next_attempt_at > now`, `last_error` non-empty) by
  querying `dlq_outbox` (new) directly.
- Metrics assertions read the three new counters via `prometheus_client REG` to confirm the
  generated/attempt-failure/terminal meters move (observability requirement of REQ-005).

## Compatibility considerations
- None (new module).

## Security considerations
- N/A.

## Rollback considerations
- Delete the module with rows 03-06.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_dlq_outbox.py`; determinism re-run 3x
  (no timing sleeps); `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.

## Completion criteria
- AC-3 and AC-4 hold under every listed crash window; no test depends on wall-clock waits.

## Out of Scope
- Promotion transaction and reconcile-class tests (row 09), shutdown join (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create module with harness + seven cases | Pending | — | — | Fails-first until rows 03-06 land |
| 2 | Determinism re-runs + mypy | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-006`, `REQ-009`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `tests/eventbus/test_eventbus_dlq_outbox.py`
