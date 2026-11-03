# Attempt-row CRUD exists in three parallel implementations, two of them unused in production

## Priority
Low

## Summary
Writing to the `attempts` table exists three times: `attempt_ops.start_attempt/finish_attempt/count_attempts` (tests-only), `StateStore.start_attempt/finish_attempt/count_attempts` (`start_attempt` and `count_attempts` have zero callers anywhere; `finish_attempt` is the only live one), and the raw `INSERT` inside `idempotency_ops.begin_stage_if_new` (the production creation path). Consolidate on one owner so lease stamping and status semantics cannot diverge between copies.

## Background
Adversarial code review of `scripts/agent/workflow/` (2026-11-03). Evidence:

- Confirmed: `scripts/agent/workflow/state_store.py:92-134` implements `start_attempt` (raw `INSERT INTO attempts` without `owner_id`/`lease_expires_at`), `finish_attempt` (raw `UPDATE attempts SET status=...`), and `count_attempts` (raw `COUNT(*)`).
- Confirmed: `scripts/agent/workflow/attempt_ops.py:42-103` implements the same three operations; its `start_attempt` additionally stamps `owner_id`/`lease_expires_at` when given `lease_duration_sec`.
- Confirmed: production callers use only `StateStore.finish_attempt` (`scripts/agent/workflow/workflow_engine.py:326,338,346,357,366`) and `idempotency_ops.begin_stage_if_new` for creation (`workflow_engine.py:308-315`; its own `INSERT INTO attempts ... owner_id, lease_expires_at` at `idempotency_ops.py:57-64`).
- Confirmed: `StateStore.start_attempt` and `StateStore.count_attempts` have no callers in `scripts/` or `tests/`. `attempt_ops.start_attempt/finish_attempt/count_attempts` are imported only by tests (`tests/agent/workflow/test_workflow_state_store.py:20`, `test_workflow_stage_persistence.py:11`, `test_workflow_engine.py:15`).
- Confirmed divergence risk: `StateStore.start_attempt` writes lease-less rows; a lease-less `running` row is only recovered under the legacy 3600-second fallback rule (`scripts/agent/workflow/state_store.py:31-33,252-253`), so any future use of that copy silently opts out of lease-based recovery.
- Related precedent: the task-side twin of this problem is `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` (open), which consolidated task CRUD on the `task_ops` side; the attempt side was never consolidated.

## Problem
Three copies of the same writes with different guarantees invite drift: a fix to attempt status semantics (e.g. the wfrecovery001 state-machine work) must be applied to every copy or the unused ones become traps. The dead `StateStore` methods are part of the public class API, so callers can pick the copy that silently skips lease stamping.

## Reason for Change
wfrecovery001 will make attempt transitions a validated state machine; consolidating the CRUD surface before or alongside that work keeps one place to enforce the contract instead of three.

## Implementation Intent
Designate one owner for attempt CRUD (the plan should decide between `attempt_ops` with `StateStore` delegating, mirroring the `task_ops` pattern already in `state_store.py:20-26`, or folding creation into the idempotency transaction deliberately). Delete or delegate the copies that do not carry lease semantics.

## Target Files or Areas
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/attempt_ops.py`
- `scripts/agent/workflow/idempotency_ops.py`
- `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`

## Required Changes
- Remove `StateStore.start_attempt` and `StateStore.count_attempts` (zero callers), or make them thin delegates to `attempt_ops` — plan decides; deletion is preferred for `start_attempt` because its lease-less SQL is a trap.
- Make `StateStore.finish_attempt` delegate to `attempt_ops.finish_attempt` (identical SQL confirmed at `state_store.py:122-125` vs `attempt_ops.py:87-93`) so the live production path shares the module implementation.
- Keep `begin_stage_if_new`'s INSERT in its `begin_immediate()` transaction (it must stay atomic with the `processed_events` check), but document explicitly why it does not call `attempt_ops.start_attempt`.
- Update the tests that import `attempt_ops.start_attempt/finish_attempt/count_attempts` only if the consolidation changes those signatures.

## Constraints
- `begin_stage_if_new` atomicity is load-bearing (single `begin_immediate()` across check + attempt insert + processed-event insert); consolidation must not split that transaction.
- `tools/generate_reference_table.py` tracks public function reference; regenerating (not hand-editing) is required after removing or delegating functions.
- Existing tests must keep passing; prefer delegation where tests call `attempt_ops` directly.

## Acceptance Criteria
- Exactly one implementation of the `INSERT INTO attempts` and `UPDATE attempts` statements remains in `scripts/` (plus the documented, transaction-bound insert inside `begin_stage_if_new` with an explicit cross-reference comment).
- No public `StateStore` method performs raw attempt SQL.
- Reference table regenerated and `--check` clean; full workflow tests and lint/type checks green.

## Testing Expectations
- Deletion/delegation verified by existing tests (`test_workflow_state_store.py`, `test_workflow_stage_persistence.py`) plus a grep-level check that no raw attempt SQL remains outside `attempt_ops.py` and `idempotency_ops.py`.
- No new behavior tests (no behavior change intended).

## Documentation Impact
Update the attempt-ops API reference entries removed or delegated via `tools/generate_reference_table.py`; note the consolidation decision in the workflow persistence docs if they list attempt CRUD entry points.

## Out of Scope
- Task-side CRUD consolidation (`wftaskapi001`).
- Changing `processed_events` semantics or attempt fencing (`wfrecovery001`).
- Schema changes to `attempts`.

## Dependencies
- `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` (open, High): sequencing decision needed — consolidate first, or let the state-machine plan absorb this consolidation.
- `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` (open): the delegation pattern chosen there should be mirrored here.

## Unresolved Questions
- 不明: whether wfrecovery001's plan already intends to own the attempt-side consolidation (its done plan lists `attempt_ops.py` and `idempotency_ops.py` procedure rows); if so this issue should be merged into that wave rather than run separately.

## AI Implementation Instruction
Consolidation only, no behavior change to the production write path. Preserve `begin_stage_if_new` transactionality exactly. Verify with the reference-table checker after deletions.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134148
- **Related target files**: `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`
