## Goal

Add end-to-end unconfirmed-visibility and repeated-shutdown tests across real processes (REQ-009, REQ-010, REQ-011), and retarget this file's 114 private-dict sets and assertions to the record registry (REQ-001; AC-1).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership; the retargeting is Phase 3 fallout)

## Assumptions
- Phase 1 tests are expected to fail until Phases 3-5 land.
- `_records` (new) comes from row 3; `ManagedProcessRecord` with `failed_start` and `last_outcome` (new) from row 2; `termination_outcome` (new) on the snapshot from row 9.
- Several tests here already use record vocabulary in their names (`test_start_reterminates_recorded_failed_start_before_restart` `:1468`, `test_start_reuses_live_process_without_record` `:1571`, `test_record_released_by_confirmed_paths` `:1680`) while asserting the three dicts; the names stay, the assertions change.

## Design decisions
- N/A: test row, no design decision of its own.

## Alternatives considered
- N/A.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
1. Add tests: a retained unconfirmed record is visible end to end (`list_processes()` and the status service), and a repeated `shutdown_all` re-terminates retained records.
2. Retarget the private-dict sets and assertions to `_records`, expressing failed-start state through the record's `failed_start` field.

### Method
Extend the existing integration module, which already exercises shutdown paths and the lifecycle logger (`:795`, `:1371-1410`). Mechanical accessor substitution across the existing classes, plus one new test class for the two end-to-end pins.

### Details
- Use the real-process fixtures already in the module; assert the retained record's pid, pgid, and outcome reach the status service (AC-1).
- Sets at `:83,103,125,140,184,198-199,213,227,242,265,291,461,494,519,533,540-541,556-557,576,1380-1381,1391-1392,1436-1437,1478,1539,1615,1650-1652,1687-1689` become `_records["test"] = ManagedProcessRecord(server_key="test", proc=proc_mock, pid=proc_mock.pid, pgid=..., state=LifecycleState.RUNNING, ...)`; the paired `_http_pgids[...] = n` lines collapse into the record's `pgid` argument.
- Add `ManagedProcessRecord` and `LifecycleState` to the import block (`:21-32`): neither is imported today, and every record fixture needs both.
- `_failed_start_procs[key] = stale_proc` at `:1478,1539,1615,1650,1690` becomes a record with `failed_start=True`; `_failed_start_procs.get(key) is stale_proc` at `:1506,1562,1636` becomes `record is not None and record.failed_start`; `... is None` at `:1568,1695` becomes `mgr._records.get("test") is None`.
- Retention assertions at `:1379-1380,1416-1417,1459-1460` (`mgr._http_procs.get("test") is proc_mock`, `mgr._http_pgids.get("test") == 7777`) become one record lookup that checks `record.proc is proc_mock` and `record.pgid == 7777`.
- `test_record_released_by_confirmed_paths` (`:1680-1726`) must give the record a confirmed outcome before calling `cleanup_server_key` and `remove_process_entry`: row 3 makes both release only when the exit is confirmed, so the fixture sets `last_outcome=TerminationOutcome.EXITED` (or `ALREADY_EXITED`) on the record it installs. The `_raise_startup_failure` branch (`:1693-1695`) keeps its release-on-confirmed behaviour unchanged.
- New `TestUnconfirmedVisibilityEndToEnd` (new) class:
  - `test_retained_record_appears_in_process_reads` (new): drive `_health_poll_until_ready` to an unconfirmed startup failure (the `:1385-1427` fixture), then assert `"test" in mgr.list_processes()`, `mgr.get_process_info("test").pid == 7777`, `.pgid == 7777`, `.running is False`, and `.termination_outcome == TerminationOutcome.EXIT_UNCONFIRMED.value` (REQ-009, AC-1).
  - `test_retained_record_appears_in_snapshot_dict` (new): same fixture, assert `mgr.get_process_snapshot("test")["termination_outcome"]` names the outcome — the dict `asdict()` produces for `scripts/agent/services/mcp_status.py` (row 10).
  - `test_repeated_shutdown_reterminates_retained_record` (new): after the retained record exists, call `await mgr.shutdown_all()` twice; assert the terminator was awaited for the server on both calls, both result lists contain `("test", TerminationOutcome.EXIT_UNCONFIRMED)`, and the record is still present after the second call (REQ-010).
  - `test_confirmed_second_pass_releases_the_record` (new): the second pass returns `TerminationOutcome.ALREADY_EXITED`; assert the record is gone and the state is confirmed (REQ-002 release condition).

## Compatibility considerations
- Test-only, but phase-coupled: the retargeting must land in the same phase as row 3, which removes the dicts. 114 sites is the largest fallout in the Plan.
- This file is the companion test for row 9 (`scripts/agent/services/models.py`): the snapshot assertions here are what validate the new `termination_outcome` field end to end.
- `tests/agent/test_http_lifecycle_shutdown_coordinator.py` (row 13) covers the coordinator's own unit behaviour; the repeated-shutdown pin here is the manager-level view and does not replace it.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_integration.py` — green after Phases 3-5 (AC-1).

## Completion criteria
- Unconfirmed visibility and repeated-shutdown behavior are pinned end to end.
- No reference to `_http_procs`, `_http_pgids` or `_failed_start_procs` remains in the file.

## Out of Scope
- The implementation changes (rows 03, 04, 09, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Tests first, expected to fail until Phases 3-5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test row: validation is the pytest run |

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
- **Requirement ID**: REQ-001, REQ-009, REQ-010, REQ-011 (defect-pinning tests first)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`
