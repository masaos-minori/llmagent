## Goal

Add end-to-end unconfirmed-visibility and repeated-shutdown tests across real processes (REQ-009, REQ-010, REQ-011), and retarget this file's 114 private-dict sets and assertions to the record registry (REQ-001; AC-1).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership; the retargeting is Phase 3 fallout)

## Assumptions
- Phase 1 tests are expected to fail until Phases 3-5 land.
- `_records` (new) comes from row 3; `ManagedProcessRecord` with `failed_start` and `last_outcome` (new) from row 2; `termination_outcome` (new) on the snapshot from row 9.
- Several tests here already use record vocabulary in their names (`test_start_reterminates_recorded_failed_start_before_restart` `:1468`, `test_start_reuses_live_process_without_record` `:1571`, `test_record_released_by_confirmed_paths` `:1680`) while asserting the three dicts; the names stay, the assertions change.
  - Corrected during execution: `test_start_reuses_live_process_without_record` and `test_start_ignores_stale_record_for_older_process` were renamed (`test_start_reuses_recorded_live_process`, `test_start_ignores_record_for_exited_process`) because the single record registry makes the two-dict scenarios (live process with no record; record naming a different live process) unrepresentable.
- Corrected during execution (stale API references in this document):
  - `ManagedProcessRecord` has no `server_key`/`proc` fields; the constructor is `ManagedProcessRecord(process=..., pid=..., pgid=..., stderr_log=..., state=..., last_outcome=None, failed_start=False)` and the process attribute is `record.process`, not `record.proc`.
  - `cleanup_server_key` and `remove_process_entry` release the record unconditionally; the confirmed-only gating lives at the call sites (ShutdownCoordinator, launcher), so the confirmed-path fixture does not seed `last_outcome`.
  - A record retained by the health-poll fixture has `poll() is None`, so the snapshot's `running` is True, not False: an unconfirmed outcome means the exit was never proven, and the retained process is by definition still possibly live.
  - `_raise_startup_failure_unconfirmed` gained an optional `outcome: TerminationOutcome | None = None` parameter and records `record.last_outcome` (defaulting to `EXIT_UNCONFIRMED`); without this the snapshot's `termination_outcome` would be None on the failed-start path and the REQ-009 pins below could not pass. This amends row 03's method signature.

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
- Sets at `:83,103,125,140,184,198-199,213,227,242,265,291,461,494,519,533,540-541,556-557,576,1380-1381,1391-1392,1436-1437,1478,1539,1615,1650-1652,1687-1689` become `_records["test"] = ManagedProcessRecord(process=proc_mock, pid=proc_mock.pid, pgid=..., state=LifecycleState.RUNNING, ...)` (executed via a `_make_record` test helper); the paired `_http_pgids[...] = n` lines collapse into the record's `pgid` argument.
- Add `ManagedProcessRecord` and `LifecycleState` to the import block (`:21-32`): neither is imported today, and every record fixture needs both.
- `_failed_start_procs[key] = stale_proc` at `:1478,1539,1615,1650,1690` becomes a record with `failed_start=True`; `_failed_start_procs.get(key) is stale_proc` at `:1506,1562,1636` becomes `record is not None and record.failed_start`; `... is None` at `:1568,1695` becomes `mgr._records.get("test") is None`.
- Retention assertions at `:1379-1380,1416-1417,1459-1460` (`mgr._http_procs.get("test") is proc_mock`, `mgr._http_pgids.get("test") == 7777`) become one record lookup that checks `record.process is proc_mock` and `record.pgid == 7777`.
- `test_record_released_by_confirmed_paths` (`:1680-1726`): `cleanup_server_key` and `remove_process_entry` release the record they find; the confirmed-only gating is enforced at the coordinator/launcher call sites (pinned in row 13's companion tests), so the fixture installs a plain record and asserts release. The `_raise_startup_failure` branch (`:1693-1695`) keeps its release-on-confirmed behaviour unchanged.
- Semantic rewrites required by the new release rule (not in the original line list): `test_start_getpgid_failure_cleans_up` now pins retention (`EXIT_UNCONFIRMED`, pgid None, stderr released); `test_shutdown_all_handles_terminate_error` and `..._terminate_timeout` now pin retention plus the returned `("test", EXIT_UNCONFIRMED)` pair; `test_restart_clears_stderr_file` seeds confirmed (`EXITED`) terminations so the restart reaches the start phase.
- New `TestUnconfirmedVisibilityEndToEnd` (new) class:
  - `test_retained_record_appears_in_process_reads` (new): drive `_health_poll_until_ready` to an unconfirmed startup failure (the `:1385-1427` fixture), then assert `"test" in mgr.list_processes()`, `mgr.get_process_info("test").pid == 7777`, `.pgid == 7777`, `.running` matching the retained process's `poll()` (True while the exit is unproven), and `.termination_outcome == TerminationOutcome.EXIT_UNCONFIRMED.value` (REQ-009, AC-1).
  - `test_retained_record_appears_in_snapshot_dict` (new): same fixture, assert `mgr.get_process_snapshot("test")["termination_outcome"]` names the outcome — the dict `asdict()` produces for `scripts/agent/services/mcp_status.py` (row 10).
  - `test_repeated_shutdown_reterminates_retained_record` (new): after the retained record exists, call `await mgr.shutdown_all()` twice; assert the terminator was awaited for the server on both calls, both result lists contain `("test", TerminationOutcome.EXIT_UNCONFIRMED)`, and the record is still present after the second call (REQ-010).
  - `test_confirmed_second_pass_releases_the_record` (new): the second pass returns `TerminationOutcome.ALREADY_EXITED`; assert the record is gone and the second result list is empty (REQ-002 release condition).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-124000 | 20261126-131906 | Tests first, expected to fail until Phases 3-5 Retargeted all dict sites via tools/retarget_http_lifecycle_integration_tests.py + hand rewrites; added TestUnconfirmedVisibilityEndToEnd; corrected stale record-API refs in this doc; extended _raise_startup_failure_unconfirmed with optional outcome arg (records last_outcome) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-131500 | 20261126-131906 | Test row: validation is the pytest run pytest 66 passed; ruff check/format clean; lint-imports 6 kept; check_module_size OK; check_docstrings no new violations; mypy clean on http_lifecycle.py + health_checker.py; companion files re-verified green (195+42 passed) |

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