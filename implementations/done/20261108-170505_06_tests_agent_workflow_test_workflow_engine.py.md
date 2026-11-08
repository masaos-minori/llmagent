## Goal
Remove the last production-side reference surface of `attempt_ops.count_attempts` from `test_workflow_engine.py`: replace its seven per-task/per-stage count asserts with a test-local inline COUNT query, and retarget the single `StateStore.pending_tool_calls` assert to the ops-level function (`REQ-001`, `REQ-004`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 6 only: `tests/agent/workflow/test_workflow_engine.py`.
- This is a Phase 1 (plan step 1) document: the edits land while the helpers still exist; the suite must be green with helpers present before documents 01-02 delete them (equivalence gate).

## Assumptions
- Call sites re-verified at HEAD `ad48bfa28`: import L15 (`from agent.workflow.attempt_ops import count_attempts`); count asserts at L221, L378, L405, L462, L622, L643, L683 (all of the shape `assert count_attempts(store._db, task.task_id, "<stage>") == <n>`); pending assert at L735 `assert len(store.pending_tool_calls(task.task_id)) == 1` in `test_fresh_pending_is_not_listed`.
- The engine's own attempt bookkeeping (`workflow_engine.py` creates attempts through `begin_stage_if_new` at L313-319 and counts retries via its loop range) is not touched; only the test-side observation helper changes.
- `SQLiteHelper` and `tool_call_state_ops` are not yet imported in this file; both imports are added (marked new below).

## Design decisions
- A module-level `_attempt_count` (new) helper mirrors the deleted `count_attempts` query one-for-one (`SELECT COUNT(*) as cnt FROM attempts WHERE task_id=? AND stage_id=?`), placed next to the existing `_attempt_error_kinds` helper (L108-125) so the two attempt-row readers sit together — the plan Assumptions keep per-task/per-stage counting test-local.
- The pending-listing assert calls `tool_call_state_ops.pending_tool_calls(store._db, task.task_id)` directly, the exact function `workflow_engine.build_turn_control_message` uses (`REQ-004`; `UNK-01`: a `wfaudit015` facade target would be assertion-equivalent).

## Alternatives considered
- Inlining the full query at all seven assert sites: rejected — seven copies of the same SQL invite the very drift this plan removes; one test-local helper keeps a single point of edit.
- Reusing `store.get_execute_attempt_count`: rejected — it filters by session and hardcodes stage `execute`, so it cannot express the per-stage counts (plan/verify) these asserts make.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
Four edits: imports, new helper, seven assert swaps, one pending-listing swap.

### Method
1. Delete the import line at L15 (`from agent.workflow.attempt_ops import count_attempts`); add to the import block: `from agent.workflow import tool_call_state_ops` (new) and `from db.helper import SQLiteHelper` (new).
2. Add `_attempt_count` (new) after the `_attempt_error_kinds` helper: parameters `(db: SQLiteHelper, task_id: str, stage_id: str) -> int`; body `rows = db.fetchall("SELECT COUNT(*) as cnt FROM attempts WHERE task_id=? AND stage_id=?", (task_id, stage_id))` then `return int(rows[0]["cnt"])`.
3. Replace each of the seven asserts (L221, L378, L405, L462, L622, L643, L683) by changing only the callee: `assert _attempt_count(store._db, task.task_id, <same stage literal>) == <same expected count>` — stages `execute` (five sites), `plan` (L622), `verify` (L643); expected counts 3, 3, 1, 1, 1, 1, 2 stay identical.
4. In `test_fresh_pending_is_not_listed`, replace L735 with `assert len(tool_call_state_ops.pending_tool_calls(store._db, task.task_id)) == 1`.

### Details
- No other call sites in this file reference the deleted helpers (census above); `store.record_tool_call`, `store.classify_stale_pending` and the `_stale_row` fixture helper survive untouched.
- `tool_call_state_ops.pending_tool_calls` is defined at `scripts/agent/workflow/tool_call_state_ops.py` L90 and is not modified by this plan.

## Compatibility considerations
- Behavior-preserving: identical SQL semantics as the deleted `count_attempts` (same tables/columns/binding), identical expected counts; `store._db` continues to be the connection argument exactly as before.
- Documents 04-05, 07-08 cover the other test files; none of them import from this file.

## Security considerations
- None.

## Rollback considerations
- Revert this document alone: HEAD calls compile until documents 01-02 delete the helpers in plan step 2.

## Validation plan
- Phase 1 equivalence gate: `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` green with the helpers still present.
- After deletion (plan step 2): the same file green; REQ-001 grep shows no `count_attempts` matches in `tests/`; full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Zero `count_attempts`/`store.pending_tool_calls` references in the file; all seven count asserts and the pending assert keep their HEAD meanings; the suite is green.

## Out of Scope
- Deleting `count_attempts` and the pending facade (documents 01-02).
- Engine internals (retry loop, `begin_stage_if_new` call) — untouched by this plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-071047 | 20261109-071047 | the test edits are the implementation; lands before documents 01-02 |
| 2 | Add or update tests per Validation plan | Completed | 20261109-071047 | 20261109-071047 | merged into step 1: helper plus assert retargets |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-071047 | 20261109-071047 | Phase 1 equivalence gate runs here with helpers still present |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-071047 | 20261109-071047 | docs grep verified zero matches; verification-only N/A: no docs/00_index.md task-scope mapping; grep zero matches for deleted helper names |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->