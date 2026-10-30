## Goal

Remove the attempt-start bypass from `StateStore`, route finishing and claiming through the canonical operations, and make stale recovery atomic and idempotent (`REQ-003`, no bypass start; `REQ-005`, terminal-only finish; `REQ-006`, atomic idempotent recovery that also fails the owning task; `REQ-010`, correct the stale comments; `REQ-012`, no bypass caller).

## Scope

- Modify only `scripts/agent/workflow/state_store.py`.
- Stale detection (`find_stale_running_attempts`, the timestamp rule) is out of scope here; it belongs to the lease Plan.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 3, after the schema row (its procedure documents `20261030-125334_10`, `_22`, and `_26` exist since 2026-10-30), rows 01-05, and after `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Phase 2 (which removes the task SQL from this file); line numbers below are from the pre-change file, so locate by symbol name.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `state_store.py` is also a target of `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (task delegation), `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (tool-call state helpers), and `plans/20261030-114516_wflease001_stale-attempt-lease.md` (detection rewrite): different methods; sequencing; the later change rebases. The lease Plan rewrites `find_stale_running_attempts`; this document keeps its signature and return shape.
- Owner decision (2026-10-30): recovery also fails the owning `running` task.
- `recover_stale_attempts` returns the recovered count and its test references (18 in 2 files) rely on that return type; it must not change.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `AttemptStatus`, `TaskStatus` (row 01 document), `AttemptTransitionError`, `TaskTransitionError` (row 02 document), `claim_task` (new), `transition_task_in_txn` (row 03 document), `mark_attempt_finished` (row 04 document).

## Design decisions

- `StateStore` stays a facade: `finish_attempt` delegates to `attempt_ops.finish_attempt` (terminal-only), `claim_task` (new) delegates to `task_ops.claim_task`; no attempt SQL remains in the facade except diagnostics.
- Recovery runs one `begin_immediate()` transaction per stale attempt: `mark_attempt_finished` to `failed` with error kind `stale_recovered` (new), then, if the task has no other `running` attempt, `transition_task_in_txn` from `running` to `failed`; an attempt that is no longer `running` (another recoverer won) is skipped, not an error.

## Alternatives considered

- One transaction for all stale attempts: rejected, one conflicting row would roll back unrelated recoveries.
- Leave the task `running`: rejected by the owner decision (the task could never be claimed again).

## Implementation

### Target file

`scripts/agent/workflow/state_store.py`

### Procedure

1. Delete `start_attempt` (`:126`).
2. Make `finish_attempt` (`:147`) delegate to the canonical `finish_attempt` in `attempt_ops` and correct its docstring (it says "Mark an attempt as completed with its final status").
3. Add `claim_task` (new)(task_id) delegating to `task_ops`.
4. Rewrite `recover_stale_attempts` (`:246`) per the Design decisions, keeping the signature `(db) -> int` and the warning and info logging; count only attempts actually transitioned.
5. Correct the docstring and comments that describe optimistic locking as the only protection and any text that implies event markers are removed on recovery.

### Method

- Detection output (`find_stale_running_attempts`, `:217`) is consumed unchanged.
- Catch `AttemptTransitionError` per attempt to count a lost race as skipped; catch `TaskTransitionError` for the task step and log it at info level without aborting the batch.
- After the per-attempt transaction the old single `db.commit()` is unnecessary; remove it.

### Details

- `count_attempts` and the diagnostic queries are untouched.
- Re-running recovery finds no `running` rows and returns 0, which is the idempotency check the recovery tests assert.

## Compatibility considerations

- `start_attempt` removal affects only tests (no production caller).
- `recover_stale_attempts` now changes task status; `agent_03_03` documents the old "never changes task status" behavior and is rewritten in its row.

## Security considerations

- N/A: parameterized SQL through the operation modules.

## Rollback considerations

- Revert the commit together with the schema row; tasks already moved to `failed` by recovery are legitimate state and need no reversal.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` (recovery, repeated recovery, race)
- `rg start_attempt scripts tests` (empty after the test rows)
- `uv run ruff format scripts/agent/workflow/state_store.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- `StateStore` has no `start_attempt`; `finish_attempt` rejects non-terminal statuses through the delegate.
- A stale attempt and its owning task are both `failed` after recovery; a second recovery changes nothing.
- No comment claims event markers are removed on recovery.

## Out of Scope

- Stale detection and leases (lease Plan), the transition API itself (row 03), tests, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `start_attempt`; delegate `finish_attempt`; add `claim_task` (new) | Pending | — | — | Plan Phase 3; gated on the schema row Blocked: schema row (attempts.attempt_number) and dbmig001 Phase 3 not landed Gated: after schema documents 20261030-125334_10, _22, _26 are executed (Plan Phase 2) |
| 2 | Rewrite `recover_stale_attempts` and fix comments | Pending | — | — |  |
| 3 | Add or update tests per Validation plan | Pending | — | — | Test rows' documents |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-003 (remove bypass start), REQ-005 (terminal-only finish), REQ-006 (atomic idempotent recovery), REQ-010 (comment corrections), REQ-012 (no bypass caller)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/state_store.py