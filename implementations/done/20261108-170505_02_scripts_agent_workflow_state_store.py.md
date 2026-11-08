## Goal
Delete the two unused `StateStore` facade methods `find_stale_running_attempts` (L174-187) and `pending_tool_calls` (L122-124) so the facade exposes only the CRUD paths production actually calls (`REQ-001`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 2 only: `scripts/agent/workflow/state_store.py`.
- This is a Phase 2 (plan step 2) document: the deletion lands only after documents 04-05 have retargeted the test callers (plan step 1, Phase 1).

## Assumptions
- Census re-verified at HEAD `ad48bfa28`: `find_stale_running_attempts` is called only from `tests/agent/workflow/test_state_store.py` L267 and `tests/agent/workflow/test_workflow_state_store.py` L528; `pending_tool_calls` on the store has ten test call sites (`test_workflow_state_store.py` L719-812, `test_workflow_engine.py` L735) and zero production callers — `workflow_engine.py` uses `tool_call_state_ops.pending_tool_calls` (defined at `tool_call_state_ops.py` L90) directly.
- Landing order per plan Dependencies/Notes: `wfaudit001` (`implementations/20261108-134201_01_scripts_agent_workflow_state_store.py.md`) then `wfaudit007` (`implementations/20261108-135741_01_scripts_agent_workflow_state_store.py.md`) then this document. Their edits live in `RecoveryReport`, `recover_stale_attempts`, `_classify_running_attempts` and the new `purge_finished_workflow_events` (new) — disjoint from this document's two deletion regions, but they shift line numbers, so these edits are anchored by symbol name, not by line number. Citations here are HEAD `ad48bfa28` anchors.
- `wfaudit015` (`plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`, Draft) may later add facades to this class; that is disjoint from these deletions (plan `UNK-01`).

## Design decisions
- Delete, not route (plan Design): the ops-level twins already exist (`attempt_ops` removal side: documents 01/03; `tool_call_state_ops.pending_tool_calls` kept) and recovery has the production entry point `recover_stale_attempts` (L189-254) built on the private `_classify_running_attempts` (L257). This mirrors the wfreview006 facade-delegation precedent named in the plan.
- Keep `_LEGACY_STALE_AGE_SEC` (L32), `RecoveryReport` (L35-42), `recover_stale_attempts`, `_classify_running_attempts`, `get_connection` (L58-65) and `finish_attempt` (L91-102) exactly as they are.

## Alternatives considered
- Keeping `find_stale_running_attempts` as a diagnostic API: rejected — nothing in `scripts/` calls it and the plan Goal is API-surface collapse; tests move to `recover_stale_attempts` behavior (document 05, `REQ-003`).

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
Delete the two facade method blocks; no other edits.

### Method
1. Delete `pending_tool_calls` (L122-124: from `def pending_tool_calls(` through `return tool_call_state_ops.pending_tool_calls(self._db, task_id)`), inside the Tool-call state section; `record_tool_call`, `finalize_tool_call` and `classify_stale_pending` stay.
2. Delete `find_stale_running_attempts` (L174-187: from `def find_stale_running_attempts(` through the closing list-comprehension `if row["classification"] == "stale"`), inside the Startup Recovery section; `recover_stale_attempts` follows directly after the section comment.

### Details
- Imports need no change: `tool_call_state_ops` (L17) is still used by the three surviving tool-call facades, `ToolCallState` (L26) is still the return type of `classify_stale_pending` (L126-132), `attempt_ops` (L17) is still used by `finish_attempt`, and `SQLiteHelper` stays in the surviving signatures.
- Deleting `find_stale_running_attempts` leaves `_classify_running_attempts` as the only classification entry; `recover_stale_attempts` already calls it directly (L205), so behavior is untouched.

## Compatibility considerations
- The two callers are test-only and land in Phase 1 (documents 04-05), so no import or attribute error occurs at any point.
- After deletion the facade surface matches the engine's real usage; `wfaudit015` plans facades for `begin_stage_if_new`/`record_artifact` — this deletion shrinks what 015 must route (plan Out-of-Scope), no conflict.

## Security considerations
- None. Removing an unused public method narrows the facade surface.

## Rollback considerations
- Revert this commit restores both one-line facades; the Phase 1 test edits are behavior-preserving and remain valid either way.

## Validation plan
- After deletion: `uv run pytest tests/agent/workflow/ -q` green, then the REQ-001 grep `grep -rn "find_stale_running_attempts\|pending_tool_calls" scripts/` — remaining matches must only be `tool_call_state_ops.py`'s definition and `workflow_engine.py`'s call of the ops-level `pending_tool_calls`.
- Full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Neither facade method exists; `recover_stale_attempts`, `classify_stale_pending` and the remaining facade surface are unchanged; all suites green.

## Out of Scope
- The test retargeting itself (documents 04-06).
- `recover_stale_attempts`/`_classify_running_attempts`/`RecoveryReport` extensions owned by `wfaudit001`/`wfaudit007`.
- New facades (`begin_stage_if_new`/`record_artifact`) owned by `wfaudit015`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-071047 | 20261109-071047 | lands after documents 04-06 (plan step 1); symbol-anchored edits |
| 2 | Add or update tests per Validation plan | Completed | 20261109-071047 | 20261109-071047 | no new tests here; coverage moved in documents 04-06 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-071047 | 20261109-071047 | includes the REQ-001 grep |
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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `scripts/agent/workflow/state_store.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->