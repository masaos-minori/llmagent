# Consolidate the two near-identical `_scalar_count` helpers in the workflow persistence layer

## Priority
Low

## Summary
Two functions implement the same `COUNT(*) as cnt` scalar read in `scripts/agent/workflow/`: the module-level `_scalar_count` in `task_ops.py` and the `StateStore._scalar_count` method in `state_store.py`. Decide one home for this helper and route both call sites through it, or leave them and record the duplication. This is a minor maintainability cleanup, not a correctness fix.

## Background
`task_ops._scalar_count(db, sql, params)` (`scripts/agent/workflow/task_ops.py:115-118`) and `StateStore._scalar_count(self, sql, params)` (`scripts/agent/workflow/state_store.py:187-190`) perform byte-for-byte the same operation: run a `COUNT(*) as cnt` query and return `int(rows[0]["cnt"]) if rows else 0`. They differ only in that the store method uses `self._db` while the ops function takes `db` explicitly. Both are small (3 lines) and used in exactly one place each. `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` collapsed other duplicated persistence API but deliberately kept "the ops-level query functions (used by the engine) intact," so this pair survived that pass untouched.

## Problem
Two copies of the same tiny helper must be kept in sync by hand. If the scalar-read contract changes (e.g. a new empty-result sentinel, a different column alias), both must be edited and neither caller is a test, so a drift would not be caught automatically. The duplication is small enough that it is mostly a code-smell than a risk, but it is exactly the kind of parallel path this project has paid for elsewhere.

## Reason for Change
It is cheap to resolve now while the persistence layer is under review, and it removes a future drift point. It is Low precisely because the blast radius is two single-use helpers and there is no evidence of current drift.

## Implementation Intent
Pick one canonical implementation and route both call sites through it:
- Prefer keeping the module-level `task_ops._scalar_count(db, ...)` as the single source and making `StateStore._scalar_count` delegate to it (`return _scalar_count(self._db, sql, params)`), since the ops function already takes an explicit `db` and mirrors the store's own style.
- Alternatively delete the `StateStore` method and inline its single caller (`get_execute_attempt_count`) onto `task_ops.get_execute_attempt_count`-style access, but only if that does not restructure the store's diagnostic section.
- Do not introduce a third location or a shared base class for two 3-line functions; that would over-engineer the fix.

## Target Files or Areas
- `scripts/agent/workflow/task_ops.py`
- `scripts/agent/workflow/state_store.py`

## Required Changes
- Reduce the two `_scalar_count` implementations to one, routing the other call site through it.
- Preserve the exact return contract: non-negative int, `0` when no rows, `int(rows[0]["cnt"])` otherwise.
- Update the one `StateStore` caller (`get_execute_attempt_count`) if the store method is removed.

## Constraints
- Behavior must be identical: same SQL shape, same empty-result handling, same `int()` coercion.
- Do not change any public store method signature or the ops function public names.
- Keep the change to these two files; do not expand scope to other persistence helpers.

## Acceptance Criteria
- A repository grep shows exactly one definition of the scalar-count logic.
- Both original call sites still resolve through the surviving helper.
- Workflow + orchestrator test packages pass unchanged.

## Testing Expectations
- Full workflow + orchestrator test packages green (the two call sites are covered by existing count-query assertions).
- ruff/mypy clean on the two touched files.

## Documentation Impact
None expected beyond the code itself. No operator-facing docs reference these private helpers.

## Out of Scope
- Removing or wiring any other persistence helper (see wfaudit009 for test-only helpers).
- Merging the two SQL insert paths or other duplication in this layer.
- Renaming public store methods.

## Dependencies
- Builds on `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` (resolved; that issue intentionally left ops-level query functions intact, which is why this pair remains).

## Unresolved Questions
- Whether to keep the module-level `task_ops._scalar_count` and delegate the store method to it, or inline the store caller directly — a small design choice best made in the plan phase. (Needs confirmation.)
- Whether consolidating two single-use helpers is worth the churn at all versus recording the duplication and leaving it. (Needs confirmation; Low priority.)

## AI Implementation Instruction
Refactor only; keep it to the two files named. Reduce the two `_scalar_count` bodies to one canonical helper and route the other call site through it, preserving the exact return contract. Verify with the existing workflow + orchestrator test suites and ruff/mypy. Do not touch other persistence helpers.

## Traceability
- **Workflow phase**: `python-code-review` (review of `scripts/agent/workflow/` and the `workflow_engine_adapter.py` integration), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-221903
- **Related target files**: `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`
