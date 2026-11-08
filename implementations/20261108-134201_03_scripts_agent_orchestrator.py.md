## Goal
Call the startup retention purge right after `recover_stale_attempts` during process initialization (REQ-003: retention runs once at startup, next to recovery).

## Scope
**Release unit**: wfaudit001-full

- Covers Plan `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` row 3 only: `scripts/agent/orchestrator.py`.

## Assumptions
- `purge_finished_workflow_events` exists as a `StateStore` method — created by the earlier-`seq` row 1 document (`20261108-134201_01_scripts_agent_workflow_state_store.py.md`).

## Design decisions
- One call, placed immediately after the existing `recover_stale_attempts` call at L92, mirroring the "called once during process initialization" convention already documented for recovery.

## Alternatives considered
- Running the purge inside `recover_stale_attempts`: rejected — separate lifecycle and reporting; the Plan specifies the wiring at the call site so each operation logs its own count.

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
Add the purge call after the existing recovery call in the initialization region (L92).

### Method
After `self._state_store.recover_stale_attempts(self._state_store.get_connection())`, call `self._state_store.purge_finished_workflow_events(self._state_store.get_connection())` (new) using the same connection; the method returns the deleted count and logs it (row 1 document).

### Details
- No new imports; no ordering constraint beyond "after recovery" — recovery must claim stale attempts before terminal-status-based deletion, which this placement guarantees.

## Compatibility considerations
- Initialization cost is one indexed DELETE per process start; negligible for the current table sizes.

## Security considerations
- N/A: no new inputs; the purge method owns all SQL (row 1 document).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Extend `tests/agent/test_orchestrator.py`: initialization invokes `purge_finished_workflow_events` once after `recover_stale_attempts` (spy/monkeypatch assertion).
- `uv run pytest tests/agent/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Every orchestrator process start performs the retention purge exactly once, after recovery, with its deleted count logged.

## Out of Scope
- The purge implementation itself (row 1 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the purge call after the recovery call (L92 region) | Pending | — | — | |
| 2 | Add the wiring test per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (startup retention purge)
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-134201
- **Related target files**: `scripts/agent/orchestrator.py`
