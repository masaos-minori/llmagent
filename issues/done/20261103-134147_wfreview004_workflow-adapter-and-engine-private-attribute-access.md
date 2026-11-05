# Workflow engine and adapter reach into private attributes of the state store and engine

## Priority
Medium

## Summary
`WorkflowEngine` and `WorkflowEngineAdapter` bypass the public seams of `StateStore` and `WorkflowEngine` by accessing private attributes (`store._db`, `self._store._db`, `self._workflow_engine._wdef`). `StateStore` already documents `get_connection()` as the sanctioned escape hatch and exposes public task methods that the adapter ignores. Route all cross-module access through public members.

## Background
Adversarial code review of `scripts/agent/workflow/` (2026-11-03). Evidence:

- Confirmed: `scripts/agent/workflow/workflow_engine.py:309` (`begin_stage_if_new(self._store._db, ...)`) and `:369` (`record_artifact(self._store._db, ...)`) — the engine reads the store's private `_db`.
- Confirmed: `scripts/agent/workflow_engine_adapter.py:301` (`create_task(store._db, ...)`), `:315` (`get_task_by_id(store._db, existing_task_id)`), and `:291,304,310,336` (`self._workflow_engine._wdef` assertions and `.version` reads) — the adapter reads private attributes of both collaborators.
- Confirmed: `scripts/agent/workflow/state_store.py:59-66` defines `get_connection()` with the docstring "Prefer using StateStore methods when possible; use this only when necessary", and `Orchestrator.__init__` already models the sanctioned use (`scripts/agent/orchestrator.py:92`, `recover_stale_attempts(self._state_store.get_connection())`).
- Confirmed: `StateStore` already has public `create_task` (`state_store.py:70-80`) and `get_task_by_id` (`:86-88`) that the adapter's direct `task_ops` calls duplicate around `store._db`.
- Confirmed: `WorkflowEngine._wdef` (`workflow_engine.py:133`) has no public accessor, yet the adapter needs its `version` in four places.
- Related precedent: the same duplication pattern on the task side is already filed as `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` (open).

## Problem
Private-attribute access freezes internal representation into external callers: any change to `StateStore._db` (connection pooling, transaction scoping) or `WorkflowEngine._wdef` (definition lifecycle, e.g. reload support under `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`) silently breaks two dependent modules, and import/type contracts cannot express the coupling. The adapter's direct `create_task(store._db, ...)` also skips `StateStore.create_task`, so a future store-level invariant (validation, transactional wiring) would be applied inconsistently.

## Reason for Change
Both classes are turn-critical integration points; the fix is mechanical, low-risk, and removes the coupling before the wfrecovery001 state-machine work changes `StateStore` internals.

## Implementation Intent
- Engine: use `self._store.get_connection()` where a raw handle is genuinely needed (`begin_stage_if_new`, `record_artifact` are transaction-level helpers), or add `StateStore` methods wrapping them so no handle leaves the store at all — plan decides which of the two per call site.
- Adapter: call `StateStore.create_task` / `StateStore.get_task_by_id` instead of `task_ops` + `store._db`, and read the workflow version through a public engine accessor (e.g. `WorkflowEngine.version` property) instead of `_wdef`.

## Target Files or Areas
- `scripts/agent/workflow/workflow_engine.py`
- `scripts/agent/workflow_engine_adapter.py`
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/models.py` (only if a public version accessor lands on `WorkflowDef` instead)

## Required Changes
- Replace `self._store._db` in `workflow_engine.py` with `self._store.get_connection()` or new `StateStore` wrapper methods.
- Replace `store._db` in `workflow_engine_adapter.py:_init_workflow_task` with `StateStore.create_task` / `StateStore.get_task_by_id` calls.
- Add a public engine-level version accessor and use it at `workflow_engine_adapter.py:291,304,310,336`.
- Keep behavior byte-identical (same SQL, same task ids, same audit payloads).

## Constraints
- No behavior change: this is encapsulation only. Task creation currently sets `turn_number=ctx.stats.stat_turns` and a fresh `workflow_id`; `StateStore.create_task` accepts the same arguments — verify signatures before rewiring.
- Tests in `tests/agent/workflow/` also touch `store._db`; migrating tests is optional and out of the critical path — do not expand scope to them unless a chosen seam makes a test unrunnable.
- Import-layer contract (`skills/DESIGN.md` Shared Vocabulary) must stay green (`lint-imports`).

## Acceptance Criteria
- No `_db` or `_wdef` access remains in `workflow_engine.py` or `workflow_engine_adapter.py` (verifiable by grep).
- All existing adapter/engine tests pass unchanged in behavior.
- `lint-imports`, ruff, mypy stay green.

## Testing Expectations
- Existing `tests/agent/workflow/test_workflow_engine.py` and orchestrator adapter tests act as the behavior lock; no new behavior tests required, but characterization coverage of `_init_workflow_task` resume-error paths (`RuntimeError` messages at `workflow_engine_adapter.py:317,319-321`) must remain passing.
- If new `StateStore` wrapper methods are added, add focused unit tests for them.

## Documentation Impact
Update the `StateStore`/`WorkflowEngine` API reference entries if new public methods or a version accessor are introduced (`docs/41_db/db_07_api_and_operations*.md` or the reference table maintained by `tools/generate_reference_table.py` — regenerate via `tools/generate_reference_table.py`, do not hand-edit).

## Out of Scope
- Consolidating `task_ops` vs `StateStore` task CRUD (owned by `wftaskapi001`).
- Changing `get_connection()`'s documented "only when necessary" wording.
- Private-attribute use inside test files.

## Dependencies
- `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` (open): coordinate direction so the adapter's task calls and the task-CRUD consolidation converge on one owner rather than diverging.
- `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` (open): its state-machine changes will touch `StateStore`; landing the seam fix first (or in the same plan wave) avoids touching the same lines twice.

## Unresolved Questions
- 不明: whether the engine's `begin_stage_if_new` / `record_artifact` calls should get dedicated `StateStore` wrapper methods (stronger encapsulation) or simply use `get_connection()` (smaller diff). Plan decision required.

## AI Implementation Instruction
Encapsulation only — identical SQL and identical public behavior. Do not rename public APIs; do not migrate test files unless a chosen seam forces it.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134147
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/workflow/state_store.py`
