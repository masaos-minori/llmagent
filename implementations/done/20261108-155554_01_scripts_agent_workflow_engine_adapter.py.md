## Goal
Remove adapter close authority over injected stores: delete the `_owns_state_store` flag and the `execute_turn` finally-close branch so the adapter never closes a store it was injected with, while `_init_workflow_task`'s method-local close of its own store stays intact (`REQ-001`/`REQ-002`), and pin the removal with a use-after-close regression test for the historical sequence (`REQ-004`).

## Scope
**Release unit**: wfaudit006-full

- Covers Plan `plans/20261108-084008_wfaudit006_state-store-lifecycle-ownership.md` row 1 only: `scripts/agent/workflow_engine_adapter.py`.
- Also hosts the `REQ-004` regression test file `tests/agent/workflow/test_adapter_store_ownership.py` (new) described in the Validation plan.

## Assumptions
- Line numbers refer to HEAD `ad48bfa28`; no sibling procedure of this batch edits this file, so they stay valid at execution time. Sibling procedures 134201_01 (wfaudit001) and 135741_01 (wfaudit007) edit other regions of `scripts/agent/workflow/state_store.py` and are design references, not implemented code.
- Production always injects the orchestrator store (`scripts/agent/orchestrator.py` injects `self._state_store` into the engine and the adapter), so the flag-close branch fires only on the direct store-less `init_workflow_task` path — consistent with the plan's Speculative failure trigger.
- Store double-close is already idempotent-safe through `SQLiteHelper` (`scripts/db/helper.py`); this procedure adds no guard (plan `REQ-005` choice, see plan Notes 2026-11-08).

## Design decisions
- Delete the flag outright instead of fixing its reset ordering: after deletion there is no per-instance state for a later turn to misread, which removes the whole failure class (plan Design "Ownership by construction, flag deletion").
- Keep the method-local `close_store` mechanism in `_init_workflow_task` (L290-293 and its finally at L321-323): the code that creates a store closes it, independent of adapter state (`REQ-002`).

## Alternatives considered
- Reset the flag inside `_init_workflow_task`'s finally right after the local close: rejected — it preserves the flag mechanism and its entire failure class; the plan's Implementation Intent mandates deletion.
- Keep the flag as a read-only audit marker: rejected — an unused attribute contradicts the ownership auditability goal (`REQ-001` acceptance: the name is absent from `scripts/`).

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
Delete the three flag statements; keep everything else byte-identical.

### Method
1. Delete the flag initialization `self._owns_state_store = False` in `__init__` (L104).
2. In the `execute_turn` finally (L254), delete the close branch `if self._owns_state_store:` and `self._state_store.close()` (L256-257) and the reset `self._owns_state_store = False` (L258). The finally keeps only `self._record_exit_status(exit_reason, error_kind, task)` (L255).
3. In `_init_workflow_task`, delete only `self._owns_state_store = True` (L294) from the store-less branch. The local `close_store = False` / `close_store = True` pair (L290-293) and the `if close_store: store.close()` finally (L321-323) stay as the only adapter-side close path (`REQ-002`).

### Details
- `grep -n "_owns_state_store" scripts/` returns nothing after this procedure (plus 02-04 completing the plan's other rows); this is the `REQ-001` acceptance check.
- The public alias `init_workflow_task` (L108-122) and its docstring (`The caller may pass a pre-opened StateStore via the store parameter`) stay unchanged; no docstring in this file mentions the flag.

## Compatibility considerations
- Direct store-less callers of `init_workflow_task` (CLI `task-init` path) keep working: their store is still created and closed by the method-local finally, so no connection leak is introduced by the flag deletion.
- Orchestrator-driven turns are behavior-identical on HEAD and after (production injects the store, so the deleted branch never fired there); only the latent use-after-close disappears.

## Security considerations
- No new attack surface: the change only removes a close operation on an injected resource.

## Rollback considerations
- Revert the commit; the flag mechanism returns with no persisted state to unwind. The new test files (this procedure's and the siblings') simply fail again on HEAD behavior.

## Validation plan
- New regression file `tests/agent/workflow/test_adapter_store_ownership.py` (new), reusing the real-wiring pattern of `tests/agent/workflow/test_session_diagnostics_wiring.py` (`_make_ctx` and `_make_orchestrator` from `tests/agent/test_orchestrator.py`, temp `workflow.sqlite` via patched `build_db_config`, patched `_run_execute_stage` and audit mocks):
  - `test_storeless_init_keeps_injected_store_usable` (new) — historical sequence: call `init_workflow_task` without the store argument on an orchestrator-hosted adapter, then run one turn through `orch._execute_turn`; after the turn assert the injected store's connection is still open (its `conn` is not `None`) and `SELECT task_id FROM tasks` on the injected connection returns the turn's row. Fails on HEAD (the finally closes the injected store, `conn` is `None`); passes after.
  - `test_storeless_init_still_closes_its_own_store` (new) — `REQ-002` pin: after the store-less `init_workflow_task`, the direct-init task row is readable through a freshly opened `StateStore` (the local finally committed and closed it cleanly), and the injected store remains usable.
- Existing direct-`init_workflow_task` and turn tests in `tests/agent/test_orchestrator.py` and `tests/integration/test_orchestrator_integration.py` stay green (`REQ-002`/plan AC).
- `uv run pytest tests/agent/ -q` after the change, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- `_owns_state_store` absent from the file and from `grep -n "_owns_state_store" scripts/` output; the `execute_turn` finally contains only the exit-status write; the method-local finally still closes locally created stores; both new tests pass and the regression test fails on HEAD.

## Out of Scope
- The orchestrator `close` method (row 2 procedure), the coordinator hook API (row 3 procedure), and the REPL registration (row 4 procedure) — same release unit, separate documents.
- `StateStore` close-guard code (demoted to no-change per plan Notes 2026-11-08; the double-close test lives in the row 2 procedure's Validation plan).
- Docs (plan Documentation Impact verified no-change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-120000 | 20261109-120000 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261109-120000 | 20261109-120000 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-120000 | 20261109-120000 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-120000 | 20261109-120000 | docs verified no-change; out of scope |

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
- **Requirement ID**: `REQ-001` (flag deletion), `REQ-002` (local close preserved), `REQ-004` (use-after-close regression)
- **Source issue**: `issues/20261107-203219_wfaudit006_state-store-lifecycle-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084008_wfaudit006_state-store-lifecycle-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-155554
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-155554 -->
