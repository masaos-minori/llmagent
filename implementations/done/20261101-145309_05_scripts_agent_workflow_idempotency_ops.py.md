<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":5,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/idempotency_ops.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Turn `scripts/agent/workflow/idempotency_ops.py` into the single canonical stage-start/finish pair: `begin_stage_if_new` starts the attempt with `attempt_number = MAX + 1` in one transaction and skips only on a completed-stage ledger row (REQ-003, REQ-004 / AC-3, AC-4).

## Scope

- Remove the `processed_events` "started" marker writes (`idempotency_ops.py:18-67`, comments `started (not completed)`).
- `begin_stage_if_new(db, event_id, task_id, stage_id)` becomes `begin_immediate`-style canonical start: ledger check → running-attempt check → `INSERT INTO attempts(..., attempt_number)` in one transaction.
- Add `finish_stage(db, ...)` counterpart that marks the attempt terminal and writes the ledger row (`event_id`, `task_id`, `stage_id`, `attempt_id`, `attempt_number`) in the same transaction.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Ledger choice is the completed-event ledger (Plan UNK-02 default): a stage is skipped only when a `processed_events` row for the (task, stage) pair exists.

## Design decisions

- Concurrent start guard: a `running` attempt for the same (task, stage) raises `StageAlreadyRunningError` before any insert; the unique index `idx_attempts_task_stage_number` (row 10) is the race backstop.
- `attempt_number` is allocated as `MAX(attempt_number)+1` over the (task_id, stage_id) pair inside the same transaction as the attempt insert (REQ-003).
- `event_id` uniqueness stays the idempotency backstop for repeated finish attempts; `result_json` stays out — `REQ-008` adds only `attempt_id`/`attempt_number`.

## Alternatives considered

- Attempt-status ledger (skip on attempt `completed` instead of a ledger row): recorded as the rejected alternative in the Plan (UNK-02) — it would drop `processed_events`, which the startup check, deploy check, and ADR name.

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`

### Procedure
1. Replace the started-marker insert with the attempts insert + numbering block.
2. Rewrite the skip check to `SELECT 1 FROM processed_events WHERE task_id=? AND stage_id=?` (ledger semantics, REQ-004).
3. Add `finish_stage` delegating the attempt update to `attempt_ops.finish_attempt` (row 04) then inserting the ledger row, one transaction.
4. Update the module docstring and the two `started (not completed)` comments (`:18-67` region).

### Method
Direct edit; function bodies rewritten, module-level names kept where callers exist.

### Details
- Engine call site: `workflow_engine.py:264` (`begin_stage_if_new`) and finish sites `:280,291,300` migrate in row 07; the function name stays stable through Phase 3.
- `event_id` generation (`workflow_engine.py:262`) is unchanged (row 07).

## Compatibility considerations

- Old databases still hold `started` marker rows; the row-26 migration rebuild decision for marker rows is governed by Plan UNK-07 (precondition fails closed and lists them) — do not silently map them.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Ledger lookups and inserts stay parameter-bound.

## Rollback considerations

- Revert with rows 04/06; the added ledger columns (row 10) tolerate the old code path, so a code revert alone is safe.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v` (row 15: double-completion skip, concurrent-start rejection).
- `uv run pytest tests/agent/workflow/test_workflow_concurrency.py -v` (row 18: numbering race).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Exactly one code path inserts an attempt; a stage re-runs after failure, skips only on a ledger row, and rejects a concurrent start with `StageAlreadyRunningError` (AC-3, AC-4).

## Out of Scope

- Ledger DDL columns (row 10) and their migration (row 26); engine retry budget (row 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Attempt lifecycle, ledger, and recovery)
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`

## Implementation Result (2026-11-03: superseded by upstream)

This wfrecovery001 procedure implemented an attempt-number-based recovery state
machine. Upstream (`origin/master`) superseded this design with a lease-based
stale-attempt recovery (wflease001, AC-2/AC-4/AC-5/AC-7). The batch was
therefore NOT merged into `origin/master`.

- **Decision (2026-11-03):** full supersession. Every one of the ~32 code files
  the batch touched was rewritten or replaced by upstream (lease columns on
  `attempts`, a `disable_foreign_keys` migration-runner rebuild, fail-closed
  tool audit, schema manifest bumped to workflow version 1.4.0). No substantive
  delta survives.
- **Action:** the 3-way merge (`git merge --no-commit backup-batch` onto branch
  `rederive` from `origin/master`) was aborted (`git merge --abort`), returning
  to a clean `origin/master` at `7d6744fd`.
- **Residual:** `attempt_number` / `CHECK` are entangled with upstream's
  lease/local-retry design and cannot be integrated as a clean, bounded
  addition; reintroducing them would fight the lease architecture.
- **Outcome:** divergent code is not integrated. The batch remains on
  `backup-batch` as a superseded historical record. All 26 procedures were
  executed and marked Completed on `backup-batch`; this note records the
  supersession.

