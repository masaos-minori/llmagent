## Goal

Turn the task methods of `scripts/agent/workflow/state_store.py` into thin delegates to `task_ops` and delete the duplicated task SQL and mapping (Plan REQ-001 canonical single implementation, REQ-002 delete zero-caller lookups).

## Scope

- Delete `StateStore`'s copies of `update_task_status`, `_row_to_task`, `get_task_by_id`, `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, `list_tasks` (currently `:63-124`).
- Keep `StateStore` method names as delegates to `task_ops` for callers the Plan keeps (`create_task` already delegates at `:51`; `update_task_status`, `get_task_by_id` delegate; `get_task_count`/`get_workflow_count` at `:210-223` delegate to the new `task_ops` functions from row 01).

## Assumptions

- `StateStore` has many test references (Plan Risks: 84 references in 7 test files) — method names must not change in this row.
- Plan overlap judgments (re-recorded 2026-11-01): toolexec001 already added the tool-call-state delegates (`:172-201`) — those are not task SQL and stay untouched; wfrecovery001/wflease001 land after this Plan and will further reshape attempt methods here (compatible by sequencing).
- Row 01 (`task_ops.py`) lands before or with this row: delegates call the functions it adds.

## Design decisions

- Delegation style mirrors the existing `create_task` delegate (`:51`): one call into `agent.workflow.task_ops`, no SQL, no row mapping in `StateStore` (AC-1: task SQL appears only in `task_ops.py` plus the two cross-table subselects `:225,239`).

## Alternatives considered

- Removing the `StateStore` task methods entirely: rejected by Plan Design (engine and tests call them; name preservation is the compatibility rule).

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Import the surviving `task_ops` functions (`update_task_status`, `get_task_by_id`, `get_task_count`, `get_workflow_count`) alongside the existing `create_task` import at `:18`.
2. Replace the bodies of `update_task_status` (`:63`), `get_task_by_id` (`:86`) with delegates; delete `_row_to_task` (`:71`), `get_task_by_idempotency_key` (`:93`), `get_task_by_session` (`:100`), `get_latest_task` (`:108`), and the `list_tasks` copy (`:118-124`).
3. Convert `get_task_count` (`:210`) and `get_workflow_count` (`:217`) to delegates of the new `task_ops` functions.

### Method
Direct edit; `find_stale_running_attempts` (`:250-277`) and `recover_stale_attempts` (`:279-316`) are attempt code outside this row's scope and stay as-is.

### Details
- `StateStore.update_task_status` is called by `workflow_engine.py:172-181`; the delegate must keep the same fire-and-forget semantics (no return).
- `session_persister.py` uses only `get_task_count`/`get_workflow_count` — delegates keep it working (REQ-001).
- The cross-table diagnostics `get_execute_attempt_count` (`:225`) and `get_artifact_uris` (`:239`) are the only task SQL allowed to remain here (REQ-001).

## Compatibility considerations

- No public name changes; the deleted `StateStore` methods have no `scripts/` caller (caller-search gate in Plan Phase 1).
- Tests calling deleted methods are removed in row 05; engine test lookups switch in row 06.

## Security considerations

- N/A: no input handling or privilege change; SQL moves verbatim into the canonical module.

## Rollback considerations

- Phase 2 commit is independently revertable per Plan phase (delegation only, no schema contact).

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` (rows 05/06 updated tests) and `uv run pytest tests/agent/test_orchestrator.py -v`.
- `rg "FROM tasks|UPDATE tasks|INSERT INTO tasks" scripts/agent/workflow` matches only `task_ops.py` and the two subselects in `state_store.py` (AC-1).
- Full `rules/toolchain.md` sequence; `PYTHONPATH=scripts uv run lint-imports` must keep 6 contracts (import direction `state_store` → `task_ops` only).

## Completion criteria

- `StateStore` contains no task row mapping, lookup, update, or aggregate SQL (only delegates and the two cross-table subselects); engine and `session_persister` behavior unchanged (AC-1, AC-2).

## Out of Scope

- Attempt methods (`start_attempt` `:128`, `finish_attempt` `:149`, `count_attempts` `:164`) and stale-recovery code (`:250-316`) — Plan Out-of-Scope; wflease001 targets them.
- Tool-call-state delegates (`:172-201`) — toolexec001-owned.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-11-01 | cycle 1 (delegation + API removal) |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-01 | row 05/06 cycle-1 test updates |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-11-01 | full suite green except 15 pre-existing lifecycle failures (fail at clean HEAD) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-01 | no docs in scope for this row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed. `create_task` delegate at `:63-71`, lookup delegates `:73-124`,
  count methods `:210-223`, migration subselects `:225,239` all confirmed.
  Zero production callers of the four lookup APIs (`rg` over `scripts/`).
- Cycle split (shared row plan 01/02/05/06): delegation rewrite and lookup
  removal run in cycle 1; the `task_nonce` kwarg rename in this file's
  signatures runs in cycle 2 with the rename unit (rows 01/03/04/12).

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (single task-persistence implementation), `REQ-002` (delete zero-caller lookups)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: scripts/agent/workflow/state_store.py