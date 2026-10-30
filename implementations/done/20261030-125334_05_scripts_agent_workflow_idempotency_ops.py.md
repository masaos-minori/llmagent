## Goal

Turn `processed_events` into a completed-stage ledger and make `begin_stage_if_new` the single attempt-start entry (`REQ-004`, completed-stage ledger and stage-already-running error; `REQ-003`, one canonical start), so that only a completed attempt can suppress a stage.

## Scope

- Modify only `scripts/agent/workflow/idempotency_ops.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 3, after the schema row (`processed_events.attempt_id` and `attempt_number`, `attempts.attempt_number`; Plan row 10, document `20261030-125334_10`) and rows 01, 02, and 04. This document MUST NOT be executed before the schema row exists.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `idempotency_ops.py` is also a target of `plans/20261030-114516_wflease001_stale-attempt-lease.md` (it passes the lease duration into the attempt-start transaction): sequencing dependency, added after this contract lands.
- Owner decision default (Plan UNK-02): completed-event ledger, not a status-bearing attempt ledger; the table name `processed_events` stays (named by the startup check, the deploy check, and ADR-001).
- `begin_stage_if_new` has 9 references in 2 test files and is named in an ADR-001 test-citation row; keeping the name limits churn.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `StageAlreadyRunningError` (row 02 document), `insert_attempt` and `mark_attempt_finished` (row 04 document).

## Design decisions

- `begin_stage_if_new` (`:18`) returns `None` only when a ledger row exists for the task-stage pair; it raises `StageAlreadyRunningError` when another attempt for the pair is `running`; otherwise it inserts a `running` attempt through `insert_attempt` and returns the `AttemptRecord` with its persisted number. No marker is written at start.
- A new function `complete_stage_attempt` (new) marks the attempt `completed` and inserts the ledger row (event id `{task_id}:{stage_id}:{attempt_number}`, with `attempt_id` and `attempt_number`) in one `begin_immediate()` transaction.
- A new `is_stage_completed` (new) answers the skip question; `is_event_processed` (`:12`) stays as the event-id lookup.

## Alternatives considered

- Status-bearing attempt ledger (drop `processed_events`): rejected for now (larger blast radius; the table is named by startup and deploy checks); recorded in the Plan Design as a later simplification.
- Writing the marker at start: rejected, that is the started-event meaning being removed.

## Implementation

### Target file

`scripts/agent/workflow/idempotency_ops.py`

### Procedure

1. Rewrite `begin_stage_if_new` with the signature `(db, task_id, stage_id, workflow_id=None)`: the `event_id` parameter is removed because the event id is now derived from the persisted attempt number (callers: the engine and tests are updated in their rows). Inside `begin_immediate()`, check `is_stage_completed` (new), then check for a `running` attempt of the pair, then call `insert_attempt` from `attempt_ops` and return its record.
2. Add `complete_stage_attempt` (new)(db, attempt): inside one `begin_immediate()` block call `mark_attempt_finished` with `completed` and insert the ledger row linked to the attempt.
3. Add `is_stage_completed` (new)(db, task_id, stage_id) as a `SELECT 1` over `processed_events`.
4. Replace the docstring and the in-function comment that describe started-event semantics and that claim recovery removes event ids with text describing the completed-stage ledger.

### Method

- Reuse the existing `AttemptRecord` return type; the engine reads the persisted `attempt_number` from it.
- Do not call `db.commit()` inside the transaction blocks.

### Details

- The `workflow_id` parameter is passed through to the attempt row only if the schema carries it for attempts; the ledger row keeps its existing `workflow_id` column, written by the same insert that the old `begin_stage_if_new` used.
- Event-id uniqueness is by the primary key; a duplicate completion for the same attempt raises through the conditional finish, not a silent insert.

## Compatibility considerations

- Behavior change: a stage whose earlier attempt failed or was recovered is no longer skipped; ADR-001 INV-08 and `agent_04_03` wording change in their own rows.
- Tests that used the started-event marker are rewritten in the test rows.

## Security considerations

- N/A: no external input.

## Rollback considerations

- Revert the commit together with the schema row; restore from the pre-migration backup if the migration already ran (forward-only).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py tests/agent/workflow/test_workflow_recovery.py tests/agent/workflow/test_workflow_concurrency.py -v`
- `uv run ruff format scripts/agent/workflow/idempotency_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- A crash that leaves a `running` attempt with no ledger row does not suppress the next run; a completed stage with a ledger row is skipped.
- Starting a stage while one attempt is `running` raises `StageAlreadyRunningError`.
- No comment in the module describes started-event semantics.

## Out of Scope

- Engine wiring, `StateStore`, DDL, tests, docs, ADR text (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `begin_stage_if_new`; add `complete_stage_attempt` (new) and `is_stage_completed` (new); fix docstrings | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 3; gated on the schema row Blocked: schema row (attempts.attempt_number) and dbmig001 Phase 3 not landed Gated: after schema documents 20261030-125334_10, _22, _26 are executed (Plan Phase 2) done in batch |
| 2 | Add or update tests per Validation plan | Completed | 20261030-183035 | 20261030-183035 | Test rows' documents done in batch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-183035 | 20261030-183035 | executed in the Plan Phase 2-4 single batch; full suite 10516 passed, 1 unrelated flaky eventbus 503 (passes alone); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-004 (completed-stage ledger and stage-already-running error), REQ-003 (one canonical attempt start)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/idempotency_ops.py