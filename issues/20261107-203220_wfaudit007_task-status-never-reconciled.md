# Reconcile task rows after stale-attempt recovery

## Priority
Medium

## Summary
Recovery marks orphaned attempts failed but leaves the owning task row permanently `running`, and no code ever writes a completed task status. Make task status reflect reality — or remove the column if nothing needs it.

## Background
Code review evidence (Verified):
- `recover_stale_attempts` updates only `attempts` (stale `running` attempts to failed); the `tasks` row keeps `running` forever.
- Grep across `scripts/`: nothing writes `completed` to `tasks.status`. The only writer besides creation is the halt path; the only reader of `tasks.status` is the halted-task guard inside the resume entry point, which today has no production caller.
- Consumers of the tasks table (session diagnostics, task counts) query by `session_id` / `workflow_id`, not by status, so crashed-vs-completed tasks are currently indistinguishable in every report.
- `docs/23_agent` turn-status descriptions (see archived `issues/done/20261103-134148_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md`) assume status carries meaning.
- Related archived incident: `issues/done/20261103-134148_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md`, `issues/done/20261021-093421_turn003_task-status-overwritten-after-failure.md` (both resolved; semantics keep drifting).

## Problem
After any crash, every affected task row reads `running` forever. Operators and diagnostics cannot tell completed tasks from crashed ones, and the halt guard on the resume path is the only logic that depends on a column the rest of the system never reconciles.

## Reason for Change
Task lifecycle state is the entry point for any future resume, retention, or operational reporting work. Leaving it unreconciled makes those features silently wrong; deciding the column is unnecessary is also a valid outcome, but only after an explicit decision.

## Implementation Intent
Complete the recovery state machine at the recovery boundary: when recovery marks a task's last attempts failed, decide the task's terminal status (e.g. mark abandoned/failed) in the same transaction. Pair this with the status-vocabulary issue so the terminal value is a declared, constrained value rather than another bare literal.

## Target Files or Areas
- scripts/agent/workflow/state_store.py (recovery path)
- scripts/agent/workflow/task_ops.py (task status writes)
- scripts/agent/diagnostic_store.py (status consumption decision, if kept)

## Required Changes
- Reconcile the owning task row whenever recovery fails its attempts.
- Define what a normal successful turn should leave as the task's terminal status (write it, or record the decision that no terminal write is wanted).
- Tests covering post-recovery task state.

## Constraints
- Recovery runs at process start and at each task-init; reconciliation must be idempotent and must not double-mark tasks already terminal.
- Concurrent processes share the workflow database; status updates must use WHERE-guarded updates like the existing lease recovery does.
- Coordinate the status vocabulary with the status-validation issue; do not invent a fourth value ad hoc.

## Acceptance Criteria
- After recovery of a crashed task, the task row no longer reads `running` (or the design explicitly documents why it may).
- A WHERE-guarded, idempotent update is used; concurrent recoveries do not conflict.
- Diagnostics/reporting behavior with the new status is stated in docs.

## Testing Expectations
- Regression test: crash simulation (running attempt + lease expiry) -> recovery -> task row terminal status asserted.
- Concurrency/idempotency test: two recoveries on the same task produce the same end state.
- Existing stale-recovery lease tests remain green.

## Documentation Impact
Document the task lifecycle states and who writes each, and the crash-recovery outcome, in the agent state-and-persistence and turn-flow docs. Correct any doc that implies task status tracks completion when it does not.

## Out of Scope
- Production wiring of the resume path.
- Retention/purge policy (separate issue).
- `attempts` semantics (already lease-based; do not change).

## Dependencies
- Depends on the vocabulary decision in `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md` for the terminal status value.
- Shares the recovery transaction with `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`; implement both reconciliations in one recovery pass if scheduled together.

## Unresolved Questions
- Is `tasks.status` worth keeping at all, given its only reader today is the test-only resume guard? (Needs confirmation with the owner before implementation.)

## AI Implementation Instruction
Reuse the existing WHERE-guarded update pattern from lease recovery. Do not add status literals outside the declared vocabulary. If the decision is to keep the column unreconciled, record that decision in docs and close this issue as a documented no-change — do not half-implement.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203220
- **Related target files**: scripts/agent/workflow/state_store.py, scripts/agent/workflow/task_ops.py, scripts/agent/diagnostic_store.py

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle).

- Claim corrected: "`completed` is never written to `tasks.status`" is stale at HEAD — the engine writes `running`/`halted`/`failed`/`completed` per run (`scripts/agent/workflow/workflow_engine.py:213-224`), and the adapter writes only `halted` for a cancelled exit (L230,273 via `_status_for_exit`). Normal turns now leave a terminal task status. — Evidence: `Verified by test` — Confidence: High
- The surviving gap is exactly the recovery reconciliation: `recover_stale_attempts` (`scripts/agent/workflow/state_store.py:190-248`) updates only `attempts`; grep for `UPDATE tasks` finds only `task_ops.update_task_status` (L68-74). A task whose process died mid-run keeps `running` forever (the engine's terminal writes never run). Crash-residual `running` rows are confirmed unreachable by any writer. — Evidence: `Verified by test` (source + grep) — Confidence: High
- Halt guard reader confirmed: the only `tasks.status` reader is the resume guard `if _fetched.status == "halted"` (`workflow_engine_adapter.py:315`) on the `existing_task_id` path; the engine's own writes read no status. — Evidence: `Verified by test` — Confidence: High
- Consumers confirmed status-agnostic: `scripts/agent/diagnostic_store.py` writes only `session_diagnostics` and never reads the `tasks` table; task counting lives in `task_ops.py:111,121` (`WHERE session_id=?`, no status filter). — Evidence: `Verified by test` — Confidence: High
- Dependency confirmed real: the terminal status value for reconciliation must come from the `wfaudit005` declared vocabulary (e.g. an abandoned/failed value), and the recovery transaction is shared with `wfaudit001`.
