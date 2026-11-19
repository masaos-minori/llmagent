## Goal

Delegate `StateStore._scalar_count` (`scripts/agent/workflow/state_store.py:187-190`) to the canonical `task_ops._scalar_count`, collapsing the two byte-for-byte-identical copies into one (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- Option A (preferred, UNK-01) is chosen: add `_scalar_count` to `state_store.py`'s existing `agent.workflow.task_ops` import (L24-30) and replace the method body with `return _scalar_count(self._db, sql, params)`.
- No circular-import risk: `state_store.py` already imports `agent.workflow.task_ops` (L24-30) and `task_ops.py` does not import `state_store.py`.
- The single caller `get_execute_attempt_count` (L207) keeps working unchanged because the delegated call has the same `(sql, params)` → `int` contract.
- The return contract is preserved exactly: non-negative int, `0` when no rows, `int(rows[0]["cnt"])` otherwise.

## Design decisions

- Replace the method body with a one-line delegation `return _scalar_count(self._db, sql, params)`, reusing the module-level canonical helper. Keep the method name and signature (`_scalar_count(self, sql, params)`) so the caller at L207 needs no change.
- Add `_scalar_count` to the existing multi-line `task_ops` import rather than adding a new import line.

## Alternatives considered

- Deleting the store method and inlining its single caller onto `task_ops` access (Option B): only if the owner prefers it; it risks restructuring the store's diagnostic section and is handled by the sibling `task_ops.py` document under Option B.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`
### Procedure
Delegate `StateStore._scalar_count` to `task_ops._scalar_count`; preserve the method name, signature, and its single caller.
### Method
1. Add `_scalar_count` to the existing import block at L24-30:
   ```python
   from agent.workflow.task_ops import (
       create_task,
       get_task_by_id,
       get_task_count,
       get_workflow_count,
       update_task_status,
       _scalar_count,
   )
   ```
2. Replace the body of `StateStore._scalar_count` (L187-190) with a one-line delegation:
   ```python
   def _scalar_count(self, sql: str, params: tuple[object, ...]) -> int:
       """Run a `COUNT(*) as cnt`-style query and return the scalar result."""
       return _scalar_count(self._db, sql, params)
   ```
   Keep the docstring (or a short note that it delegates) so the diagnostic section stays readable.
3. Leave `get_execute_attempt_count` (L207) untouched — it still calls `self._scalar_count(...)`.
### Details

- Preserve the exact return contract; do not alter the `COUNT(*) as cnt` shape or the `int(rows[0]["cnt"]) if rows else 0` semantics (now owned by `task_ops._scalar_count`).
- Do not change any public store method signature (REQ-002).
- If Option B is selected instead, delete this method here and inline `get_execute_attempt_count`'s call via `task_ops` access in the sibling document.

## Compatibility considerations

N/A: private helper delegation; no public signature change (REQ-002).

## Security considerations

N/A: no change to query construction or parameter binding; the same parameterized query runs.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Static: format, lint, types | `uv run ruff format --check scripts/agent/workflow/state_store.py`; `uv run ruff check scripts/agent/workflow/state_store.py`; `uv run mypy --no-namespace-packages scripts/` | ruff/mypy clean |
| workflow + orchestrator test packages | Unit: `test_get_execute_attempt_count_filters_by_stage` still passes through the delegated helper | `uv run pytest tests/agent/workflow/ tests/agent/test_session_persister.py -v` | Passes; exactly one scalar-count definition remains (AC-1, AC-2) |

## Completion criteria

- `StateStore._scalar_count` delegates to `task_ops._scalar_count`; both original call sites resolve through the surviving helper (AC-2).
- Exactly one workflow-persistence `_scalar_count` definition remains (AC-1).
- `test_get_execute_attempt_count_filters_by_stage` and the rest of the workflow + orchestrator packages pass unchanged (T-1).
- ruff/mypy clean on `scripts/agent/workflow/state_store.py` (T-2).

## Out of Scope

- Removing or wiring any other persistence helper.
- Renaming public store methods (REQ-002).
- Touching the other `_scalar_count` helpers (`scripts/db/store_impl.py`, `scripts/agent/memory/count_ops.py`).
- Changing `session_persister.py` or its tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delegate `StateStore._scalar_count` to `task_ops._scalar_count` (`scripts/agent/workflow/state_store.py`, REQ-001) | Completed | 20261119-102031 | 20261119-102031 | — |
| 2 | Verify exactly one definition remains (`scripts/agent/workflow/state_store.py`, REQ-002) | Completed | 20261119-102031 | 20261119-102031 | — |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261118-221903_wfrev003_duplicate-scalar-count.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-233732_wfrev003_duplicate-scalar-count.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-071847
- **Related target files**: `scripts/agent/workflow/state_store.py`
