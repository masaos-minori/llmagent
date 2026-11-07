# Prune processed_events on recovery and add workflow retention

## Priority
High

## Summary
Stage idempotency rows in `processed_events` are never deleted anywhere, while the recovery code comments claim they are. Fix the false recovery claims and make recovery reconcile `processed_events` so a recovered stage is not permanently skipped; add a retention story for the workflow tables.

## Background
Code review of the workflow domain (Verified evidence):
- The `begin_stage_if_new` docstring states that stale attempts are detected and "removes their event IDs" so they run again.
- The adapter comment before stage-definition build claims "crashed tasks will not produce duplicate stage executions".
- No `DELETE FROM processed_events` exists anywhere in `scripts/` (grep-verified). The dedup store has `DedupStore.purge_expired`; the workflow domain has no purge at all.
- The event key is deterministic (`task_id:stage_id:attempt`), so a resumed task re-running attempt N collides with the surviving row.
Related archived work: `issues/done/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md` reorganized attempt CRUD but did not add pruning.

## Problem
- After a crash, `recover_stale_attempts` marks attempts failed but the event rows survive. A later execution of the same task+stage+attempt key gets `begin_stage_if_new` returning None, and the engine treats the stage as "duplicate (already completed)" success without executing it — a silent stage skip.
- The table grows about three rows per turn forever with no retention, unlike the dedup store.

## Reason for Change
The code documents a safety property it does not implement. Today the permanent-skip path is only reachable through the task-resume entry point, but that entry point exists in the adapter API; once it is wired, the trap ships silently. Table growth is already unbounded on the production database.

## Implementation Intent
Recovery owns reconciliation: whichever component marks an attempt failed must also remove that attempt's `processed_events` row, so idempotency state and attempt state always agree. Separately, the workflow persistence boundary needs a retention policy (mirroring the dedup store's purge) or an explicit decision that growth is acceptable. Docstrings and comments must state actual behavior, not intended behavior.

## Target Files or Areas
- scripts/agent/workflow/idempotency_ops.py
- scripts/agent/workflow/state_store.py (recovery path)
- scripts/agent/workflow_engine_adapter.py (recovery comment)
- docs/41_db (workflow retention statements)

## Required Changes
- Remove event rows for attempts that recovery marks failed (same transaction as the attempt update).
- Correct the `begin_stage_if_new` docstring and the adapter comment to match implemented behavior.
- Define a retention/purge policy for `processed_events` (and `tasks` / `attempts` / `artifacts`), or record the no-purge decision explicitly in the docs.

## Constraints
- Prune and attempt-fail marking must commit atomically; a crash between them must not leave an attempt failed while its event row survives.
- Do not weaken the dedup guard for stages that genuinely completed.
- No incremental schema migration is allowed for workflow.sqlite (migrations were retired); retention must not require schema changes without a recreate path.

## Acceptance Criteria
- Recovery of a stale attempt removes its event row; a subsequent `begin_stage_if_new` for the same key proceeds (returns a row, not None).
- Docstring and adapter comment describe only implemented behavior.
- A documented retention policy (or explicit no-purge decision) exists for the workflow tables.

## Testing Expectations
- Regression test: running attempt with a written event row -> `recover_stale_attempts` -> next `begin_stage_if_new` on the same event key must not skip.
- Existing stage-dedup tests remain green.
- If retention is added: unit test for the purge boundary and a docs consistency check.

## Documentation Impact
`docs/41_db` workflow-database pages must state the retention behavior (or the deliberate absence of one) and the recovery reconciles-attempt-and-event-state invariant. Remove or never introduce claims that recovery prunes events unless implemented.

## Out of Scope
- Changing the event key format.
- Wiring the task-resume entry point into production.
- Rewriting the engine retry loop.

## Dependencies
- Review alongside `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md` (same recovery path; reconcile both tables together).
- Context: `issues/done/20261103-134148_wfreview006_duplicate-attempt-crud-apis.md` (resolved; re-verify current source after it).

## Unresolved Questions
- Is the task-resume path (`existing_task_id`) intended for production wiring? Determines how urgent the permanent-skip trap is (Needs confirmation).
- Should retention purge cover all workflow tables or only `processed_events`?

## AI Implementation Instruction
Keep the change inside the recovery/idempotency boundary: attempt-state and event-state writes must stay in one transaction. Do not modify the engine skip logic. Fix the misleading docstring in the same commit as the behavior change, and update docs only for the retention decision.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203214
- **Related target files**: scripts/agent/workflow/idempotency_ops.py, scripts/agent/workflow/state_store.py, scripts/agent/workflow_engine_adapter.py, docs/41_db

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle).

- `begin_stage_if_new` misleading statement confirmed, with one location correction: the "recovery ... removes their event IDs" statement is an in-function comment block (`scripts/agent/workflow/idempotency_ops.py:43-46`), not the docstring. — Evidence: `Verified by test` (source read) — Confidence: High
- Adapter comment corrected: no "crashed tasks will not produce duplicate stage executions" comment exists anymore — the adapter has zero `processed_events`/`event_id` references today (grep at HEAD `926dbc109`; likely removed by `dee33ce7b fix(wfreview004)`). Only the idempotency_ops comment needs correcting. — Evidence: `Verified by test` (grep) — Confidence: High
- `DELETE FROM processed_events` confirmed absent across `scripts/` (grep exit 1). `recover_stale_attempts` (`scripts/agent/workflow/state_store.py:190-248`) updates `attempts` to failed with a WHERE-guarded compare-and-swap and commits — no event-row reconciliation. — Evidence: `Verified by test` — Confidence: High
- Permanent-skip trap confirmed live: engine builds `event_id = f"{task_id}:{stage_id}:{attempt}"` (`scripts/agent/workflow/workflow_engine.py:311`), and on `begin_stage_if_new` returning None logs "Stage ... skipped (already processed)" and returns without executing (`workflow_engine.py:321-325`). — Evidence: `Verified by test` — Confidence: High
- `DedupStore.purge_expired` exists as the retention precedent (`scripts/shared/mcp_dedup.py:313`). — Evidence: `Verified by test` — Confidence: High
- Adjacent fact: the engine now calls `begin_stage_if_new` with `self._store.get_connection()` (`workflow_engine.py:314`) — the facade-bypass pattern separately filed as `wfaudit015`; a prune change here touches the same call path.
