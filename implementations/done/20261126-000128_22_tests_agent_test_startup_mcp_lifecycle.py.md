## Goal

Keep the startup-orchestrator regression test driving a real `HttpServerLifecycleManager` after row 3 removes the three tracking dicts, by expressing its fixtures and assertions through the record registry (REQ-001; AC-5).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan's `R3-ownership` unit lists Phases 3 and 4; this row is cited by Phase 3)

## Assumptions

- `_records` (new) comes from row 3; `ManagedProcessRecord` with `failed_start` and `last_outcome` (new) from row 2. (Corrected 2026-11-26 during execution: there is no `set_termination_outcome` API; the outcome lives on `record.last_outcome`, set via `settle()` or `_raise_startup_failure_unconfirmed`.)
- The test's intent is unchanged: `test_unconfirmed_first_failure_raises_not_records_spawn` (`:281-361`) pins that an unconfirmed first attempt ends in `HttpStartupError` and a retained process, not in a recorded spawn.
- `startup._mcp_starter._spawned_subprocesses == []` (`:352`) and the terminator-window assertions (`:356-360`) are unrelated to the dicts and stay as they are.

## Design decisions

- Simulate the launcher by installing a record, not by patching the manager's internals: `_fake_create` (`:304-308`) stands in for `create_and_validate_proc`, which row 5 makes the registration point, so the fake must produce the same object the real launcher produces.
- Assert retention through one record (`record.process`, `record.failed_start`, `record.last_outcome`) instead of two dict lookups, which is the point of REQ-001.

## Alternatives considered

- Drop the manager-level assertions and assert only the raised error — rejected: the retained process is half of what the test pins (the other half is "not recorded as a spawn").

## Implementation
### Target file
`tests/agent/test_startup_mcp_lifecycle.py`
### Procedure
1. Rewrite `_fake_create` (`:304-308`) to register a `ManagedProcessRecord`.
2. Rewrite `_start_http_subprocess`'s return (`:324-328`) to read the record.
3. Rewrite the retention assertions (`:353-354`) as one record assertion.
### Method
Three edits inside one test function plus two new imports; the other 20 tests in the file are untouched.

### Details

- `_fake_create` becomes: `mgr._records[server_key] = ManagedProcessRecord(process=fake_proc, pid=fake_proc.pid, pgid=99001, stderr_log=None, state=LifecycleState.RUNNING)` and still returns `(fake_proc, MagicMock())` for the stderr handle. (Corrected 2026-11-26: the dataclass has no `server_key`/`proc` fields; the process field is `process`.)
- `_start_http_subprocess` returns `record.process if (record := mgr._records.get(server_key)) is not None else None`, keeping the "no process returned" contract the starter already handles (`test_no_process_returned_does_not_append` at `:158`).
- Retention assertions become: `record = mgr._records.get("web")`; `record is not None`; `record.process is fake_proc`; `record.failed_start is True`; `record.last_outcome is TerminationOutcome.EXIT_UNCONFIRMED` — the last one holds because `_raise_startup_failure_unconfirmed` records the outcome on the retained record (default `EXIT_UNCONFIRMED` when the caller passes none), as called from `_fake_health` (`:318-321`) and the retry's re-termination path.
- Add `from agent.http_lifecycle_process_record import ManagedProcessRecord` and `from agent.lifecycle import LifecycleState` to the import block (`:15-27`); `TerminationOutcome` is already imported (`:16-20`).

## Compatibility considerations

- Phase-coupled with row 3: this file must be retargeted in the same phase that removes the dicts, otherwise the suite breaks between the two commits. Rows 5 and 6 drive the same startup path, so their validation runs must stay green alongside it.
- Corrected 2026-11-26 (row 06 verification): the starter-side private-dict assignments are NOT inert — `tests/agent/test_startup_mcp_starter.py` `_real_router_ctx` drives the real router, whose `start_http_subprocess` now reads `_records` (row 06), so its fake manager was retargeted to `_records` with a `ManagedProcessRecord` during row 06's cycle; `tests/agent/test_agent_factory.py:433,490` fixtures were likewise retargeted to `_records = {}` because AsyncMock's auto-created `_records.get` returned a coroutine against the rewired router.

## Security considerations

N/A: test-only change.

## Rollback considerations

Revert this row together with rows 2 and 3: the record type and registry are what the rewritten fixtures require.

## Validation plan

- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py` — green before this row, and green after it lands together with rows 2-3 and 5.
- `uv run ruff check tests/agent/test_startup_mcp_lifecycle.py` per `rules/toolchain.md`.

## Completion criteria

- No reference to `_http_procs`, `_http_pgids` or `_failed_start_procs` remains in the file.
- The unconfirmed-failure test asserts one retained record with `failed_start` and the unconfirmed outcome.

## Out of Scope

- The launcher's own registration order (row 5, validated by `tests/agent/test_http_lifecycle.py`).
- The starter's retry and shutdown-event behaviour, which this file pins through mocks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-132000 | 20261126-132049 | _fake_create installs a ManagedProcessRecord; _start_http_subprocess reads record.process; retention asserted through one record; stale API refs corrected in this doc |
| 2 | Add or update tests per Validation plan | Completed | 20261126-132000 | 20261126-132049 | Existing test rewritten in place; no new tests required by the procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-132100 | 20261126-132049 | pytest 21 passed; ruff check/format clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only row; docs covered by rows 19-23 |

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
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-000128
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`