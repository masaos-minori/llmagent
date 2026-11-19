## Goal

Retain `task_ops._scalar_count` (`scripts/agent/workflow/task_ops.py:115-118`) as the single canonical implementation of the workflow-persistence scalar-count helper, so the two previously byte-for-byte-identical copies collapse to one (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- Option A (preferred, UNK-01) is chosen: `task_ops._scalar_count` stays as the canonical home and `StateStore._scalar_count` delegates to it. If the owner instead selects Option B (delete this helper, inline `get_execute_attempt_count`), this document's instruction becomes "delete the helper" and `state_store.py`'s document handles the inline — see `Plan Gap` note below.
- No circular-import risk: `state_store.py` already imports `agent.workflow.task_ops` (L24-30) and `task_ops.py` does not import `state_store.py`.
- The return contract is preserved exactly: non-negative int, `0` when no rows, `int(rows[0]["cnt"])` otherwise.

## Design decisions

- Keep the module-level function signature `_scalar_count(db, sql, params)` unchanged (no public-name change, REQ-002). Its body is retained verbatim as the canonical definition.
- The two internal callers (`get_task_count` at L123, `get_workflow_count` at L132) are unaffected and continue calling this helper.

## Alternatives considered

- Deleting this helper (Option B): rejected by default because it forces inlining `get_execute_attempt_count` onto `task_ops` access and risks restructuring the store's diagnostic section; only choose if the owner prefers it.

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`
### Procedure
Under Option A this file needs no body change — establish it as the single surviving definition and confirm both original call sites resolve through it.
### Method
1. Confirm the body at L115-118 is retained unchanged:
   ```python
   def _scalar_count(db: SQLiteHelper, sql: str, params: tuple[object, ...]) -> int:
       """Run a `COUNT(*) as cnt`-style query and return the scalar result."""
       rows = db.fetchall(sql, params)
       return int(rows[0]["cnt"]) if rows else 0
   ```
2. Confirm the two internal callers still reference it: `get_task_count` (L123) and `get_workflow_count` (L132).
3. Confirm no second workflow-persistence copy of this logic exists anywhere (the `StateStore._scalar_count` copy is removed/delegated by the sibling `state_store.py` document; `store_impl.py:24` and `count_ops.py:7` have different signatures and stay out of scope).
### Details

- Do not rename the function or change its signature (REQ-002).
- If Option B is selected instead, delete this helper and route its two callers through `task_ops` access via the store — only after the `state_store.py` document inlines `get_execute_attempt_count` without restructuring the diagnostic section.

## Compatibility considerations

N/A: private helper only; no public signature or ops public-name change (REQ-002).

## Security considerations

N/A: no change to query construction or parameter binding.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | Static: format, lint, types | `uv run ruff format --check scripts/agent/workflow/task_ops.py`; `uv run ruff check scripts/agent/workflow/task_ops.py`; `uv run mypy --no-namespace-packages scripts/` | ruff/mypy clean |
| workflow + orchestrator test packages | Unit: existing count-query assertions still pass through the surviving helper | `uv run pytest tests/agent/workflow/ tests/agent/test_session_persister.py -v` | Passes; exactly one scalar-count definition remains (AC-1, AC-2) |

## Completion criteria

- Exactly one workflow-persistence `_scalar_count` definition remains (AC-1).
- Both original call sites (`task_ops.get_task_count`/`get_workflow_count` and `StateStore.get_execute_attempt_count`) resolve through the surviving helper (AC-2).
- ruff/mypy clean on `scripts/agent/workflow/task_ops.py` (T-2).

## Out of Scope

- Removing or wiring any other persistence helper.
- Merging the two SQL insert paths or other duplication in this layer.
- Renaming public store methods or the ops public names (REQ-002).
- Touching the other `_scalar_count` helpers (`scripts/db/store_impl.py`, `scripts/agent/memory/count_ops.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retain `task_ops._scalar_count` as the canonical home (`scripts/agent/workflow/task_ops.py`, REQ-001) | Completed | 20261119-102031 | 20261119-102031 | — |
| 2 | Verify exactly one definition remains (`scripts/agent/workflow/task_ops.py`, REQ-002) | Completed | 20261119-102031 | 20261119-102031 | — |

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
- **Related target files**: `scripts/agent/workflow/task_ops.py`
