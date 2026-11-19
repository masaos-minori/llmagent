## Goal
- Consolidate the two near-identical `_scalar_count` helpers in the workflow persistence layer (`scripts/agent/workflow/task_ops.py` and `scripts/agent/workflow/state_store.py`) into one canonical helper and route both call sites through it, preserving the exact return contract.

## Priority
Low

## Scope
- **In-Scope**: Reduce the two byte-for-byte-identical `_scalar_count` bodies (module-level `task_ops._scalar_count` and `StateStore._scalar_count`) to one canonical implementation and route the other call site through it, within `scripts/agent/workflow/task_ops.py` and `scripts/agent/workflow/state_store.py` only.
- **Out-of-Scope**: Removing or wiring any other persistence helper; merging the two SQL insert paths or other duplication in this layer; renaming public store methods; touching the other `_scalar_count` helpers (`scripts/db/store_impl.py`, `scripts/agent/memory/count_ops.py`), which have different signatures and are not duplicates of this pair.
- **Dependencies**: Builds on `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` (resolved; that issue intentionally left ops-level query functions intact, which is why this pair remains).
  - **Depends on**: N/A: none

## Background
`task_ops._scalar_count(db, sql, params)` (`scripts/agent/workflow/task_ops.py:115-118`) and `StateStore._scalar_count(self, sql, params)` (`scripts/agent/workflow/state_store.py:187-190`) perform byte-for-byte the same operation: run a `COUNT(*) as cnt` query and return `int(rows[0]["cnt"]) if rows else 0`. They differ only in that the store method uses `self._db` while the ops function takes `db` explicitly. Both are small (3 lines). `StateStore._scalar_count` has exactly one caller (`get_execute_attempt_count`, `state_store.py:207`); `task_ops._scalar_count` has two callers within `task_ops.py` (`get_task_count` at L123 and `get_workflow_count` at L132). `issues/done/20261107-203222_wfaudit009_test-only-state-helpers.md` collapsed other duplicated persistence API but deliberately kept "the ops-level query functions (used by the engine) intact," so this pair survived that pass untouched. Note: `scripts/db/store_impl.py` and `scripts/agent/memory/count_ops.py` each define their own `_scalar_count` with a different signature; they are not duplicates of this pair and are out of scope.

## Problem
Two copies of the same tiny helper must be kept in sync by hand. If the scalar-read contract changes (e.g. a new empty-result sentinel, a different column alias), both must be edited and neither caller is a test, so a drift would not be caught automatically. The duplication is small enough that it is mostly a code-smell than a risk, but it is exactly the kind of parallel path this project has paid for elsewhere.

## Reason for Change
It is cheap to resolve now while the persistence layer is under review, and it removes a future drift point. It is Low precisely because the blast radius is two single-use helpers and there is no evidence of current drift.

## Implementation Intent
Pick one canonical implementation and route both call sites through it:
- **Preferred**: Keep the module-level `task_ops._scalar_count(db, ...)` as the single source and make `StateStore._scalar_count` delegate to it (`return _scalar_count(self._db, sql, params)`). This is clean: `state_store.py` already imports several functions from `agent.workflow.task_ops` (L24-30), so adding `_scalar_count` to that existing import introduces no circular-import risk (`task_ops.py` does not import `state_store.py`).
- **Alternative**: Delete the `StateStore` method and inline its single caller (`get_execute_attempt_count`) onto `task_ops` access — only if that does not restructure the store's diagnostic section.
- Do not introduce a third location or a shared base class for two 3-line functions; that would over-engineer the fix.

## Requirements
- `REQ-001`: Reduce the two byte-for-byte-identical `_scalar_count` implementations to one canonical helper, routing the other call site through it, and preserve the exact return contract (non-negative int, `0` when no rows, `int(rows[0]["cnt"])` otherwise).
- `REQ-002`: Do not change any public store method signature or the ops function public names, and confine the change to `scripts/agent/workflow/task_ops.py` and `scripts/agent/workflow/state_store.py`.

## Implementation Target Files
**Freeze status**: Frozen (set from `Draft` after `issue-to-plan` Step 8's
Implementation Target Files Validation passed — `audit_plan_target_paths.py` reports
0 findings; both rows are `Verified`).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | Modify — retain as the canonical home for `_scalar_count` (Option A) or remove it (Option B); no public-name change | REQ-001, REQ-002 | `task_ops._scalar_count` L115-118 is byte-for-byte identical to `StateStore._scalar_count`; 2 internal callers (L123, L132) (checked in Step 2/3) | `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/test_session_persister.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Modify — delegate `StateStore._scalar_count` to `task_ops._scalar_count` (Option A) or delete it and inline its caller (Option B); add `_scalar_count` to the existing `task_ops` import (L24-30) | REQ-001, REQ-002 | `StateStore._scalar_count` L187-190 has one caller (`get_execute_attempt_count` L207); `state_store.py` already imports from `task_ops` (no circular import) (checked in Step 2/3) | `tests/agent/workflow/test_workflow_state_store.py::test_get_execute_attempt_count_filters_by_stage` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/store_impl.py` | Confirm its `_scalar_count` (L24, signature `(db, sql)`) is a different helper, not a duplicate of this pair, so it stays out of scope. | REQ-002 |
| `scripts/agent/memory/count_ops.py` | Confirm its `_scalar_count` (L7, signature `(sql, params=())`) is a different helper, not a duplicate of this pair, so it stays out of scope. | REQ-002 |
| `scripts/agent/session_persister.py` | Read `get_execute_attempt_count`'s production caller (L97) to confirm delegating/removing the store method preserves the return contract it relies on. | REQ-001 |

## Acceptance Criteria
- **AC-1 (REQ-001)**: A grep for the workflow-persistence scalar-count pattern (`int(rows[0]["cnt"]) if rows else 0` over a `COUNT(*) as cnt` query) shows exactly one definition after consolidation.
- **AC-2 (REQ-001)**: Both original call sites (`task_ops.get_task_count`/`get_workflow_count` and `StateStore.get_execute_attempt_count`) still resolve through the surviving helper.
- **AC-3 (REQ-002)**: Workflow + orchestrator test packages pass unchanged; no public store method signature or ops public name changed.

## Tests
- **T-1 (REQ-001, REQ-002)**: Full workflow + orchestrator test packages green (the two call sites are covered by existing count-query assertions, e.g. `test_get_execute_attempt_count_filters_by_stage`).
- **T-2 (REQ-002)**: ruff/mypy clean on `scripts/agent/workflow/task_ops.py` and `scripts/agent/workflow/state_store.py`.

## Documentation Impact
None expected beyond the code itself. No operator-facing docs reference these private helpers.

## Assumptions
- Option A (delegate) is chosen unless the owner prefers Option B; either preserves behavior.
- Adding `_scalar_count` to `state_store.py`'s existing `task_ops` import (L24-30) is sufficient; no new import line is required.
- The refactor changes no public signature, so `session_persister.py` and its tests need no change.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to keep the module-level `task_ops._scalar_count` and delegate `StateStore._scalar_count` to it (preferred; no circular-import risk since `state_store.py` already imports `task_ops`), or delete the store method and inline its single caller (`get_execute_attempt_count`). | None missing; both preserve behavior. Owner decides during `plan-to-implementation-procedure`. | Preferred = Option A (delegate). | False |
| UNK-02 | Whether consolidating two single-use 3-line helpers is worth the churn versus recording the duplication and leaving it. | None missing; owner preference. Low priority. | Owner decides; if left, record the duplication note instead of refactoring. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

Blast Radius is judged qualitatively (Path A): the change is two private 3-line helpers with no public-signature or schema impact. `Churn (30d)` and `Bus Factor` are `N/A` because Path A skips the historical analysis.

## Design
Classification: **Path A** (see `skills/issue-to-plan/SKILL.md` Routing). Modification scope is 2 files, no public/runtime interface change (both helpers are private; no public signature changes), no DB-schema change. Step 2/3 verified: the two bodies are byte-for-byte identical except `db` vs `self._db`; `StateStore._scalar_count` has one caller (`get_execute_attempt_count`), `task_ops._scalar_count` has two internal callers; `state_store.py` already imports `task_ops` (L24-30), so delegating introduces no circular-import risk. The two other repo-wide `_scalar_count` helpers (`store_impl.py`, `count_ops.py`) have different signatures and are not duplicates, so they stay out of scope.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Consolidate the two `_scalar_count` bodies** (`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, REQ-001)
   - [ ] Resolve UNK-01 (default: Option A — keep `task_ops._scalar_count` canonical).
   - [ ] Under Option A: add `_scalar_count` to the existing `task_ops` import in `state_store.py` (L24-30) and replace `StateStore._scalar_count`'s body with `return _scalar_count(self._db, sql, params)`; under Option B: delete `StateStore._scalar_count` and inline its caller via `task_ops` access without restructuring the diagnostic section.
   - [ ] Preserve the exact return contract: non-negative int, `0` when no rows, `int(rows[0]["cnt"])` otherwise.
2. **Phase 2: Verify** (`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, REQ-002)
   - [ ] Confirm exactly one definition of the workflow-persistence scalar-count logic remains and both original call sites resolve through it.
   - [ ] Run the workflow + orchestrator test packages; ruff/mypy clean on both files.

### Release units
N/A: no release unit — the consolidation validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py` | Static: format, lint, types | `uv run ruff format --check scripts/agent/workflow/task_ops.py scripts/agent/workflow/state_store.py`; `uv run ruff check scripts/agent/workflow/task_ops.py scripts/agent/workflow/state_store.py`; `uv run mypy --no-namespace-packages scripts/` | ruff/mypy clean |
| workflow + orchestrator test packages | Unit: existing count-query assertions still pass through the surviving helper | `uv run pytest tests/agent/workflow/ tests/agent/test_session_persister.py -v` | Passes; exactly one scalar-count definition remains |

## Risks
- **Risk**: Option A introduces a circular import between `state_store.py` and `task_ops.py`. → **Mitigation**: verified `state_store.py` already imports `task_ops` (L24-30) and `task_ops.py` does not import `state_store.py`; no cycle. Re-check with `lint-imports` in T-2.
- **Risk**: Accidentally changing the return contract (empty-result sentinel, column alias, `int()` coercion) while consolidating. → **Mitigation**: preserve the exact body semantics; AC-1/AC-2 and the count-query test assertions verify it.
- **Risk**: Scope creep into the other two `_scalar_count` helpers (`store_impl.py`, `count_ops.py`). → **Mitigation**: constrain to the two workflow-persistence helpers (REQ-002); their different signatures make them non-duplicates.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Consolidate the two `_scalar_count` bodies (`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, REQ-001) | Completed | — | 20261119-102147 |  |
| 2 | Phase 2: Verify consolidation (`scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, REQ-002) | Completed | — | 20261119-102147 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-071847_01_scripts_agent_workflow_task_ops.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261119-071847_02_scripts_agent_workflow_state_store.py.md | 1, 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-221903_wfrev003_duplicate-scalar-count.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-233732
- **Related target files**: `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Implementation Intent | `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py` | Step 1 | AC-1, AC-2 | T-1 | Confirmed by repository evidence |
| REQ-002 | Constraints; Required Changes bullet 3 | `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py` | Step 2 | AC-3 | T-2 | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-071847 -->
