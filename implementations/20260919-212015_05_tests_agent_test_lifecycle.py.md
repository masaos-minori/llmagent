## Goal
Update every assertion/fixture-setup in this file that reads or writes
`HttpServerLifecycleManager._stderr_log_paths` directly, so the file keeps testing
the same behavior after Step 02 of this pass removes that attribute (`REQ-001`).

## Scope
- In scope: the 7 call sites confirmed by `rg "_stderr_log_paths" tests/agent/test_lifecycle.py`
  — lines 455, 483 (`mgr._http_mgr._stderr_log_paths`, read-only assertions in two
  getpgid-failure test methods inside `TestStartHttpSubprocess`, current lines
  166-486), 832 (fixture write in `test_restart_closes_old_stderr_handle`),
  1191, 1204, 1213 (fixture writes in `TestCleanupServerResources`), and 1197
  (read-only assertion in `TestCleanupServerResources.test_removes_last_health_check_entry`).
- Out of scope: any other test in this file; any change to what each test verifies
  (only how it reads/writes the now-relocated tracking data).

## Assumptions
- Step 02 of this pass
  (`implementations/20260919-212015_02_scripts_agent_http_lifecycle.py.md`) removes
  `HttpServerLifecycleManager._stderr_log_paths` and routes all reads/writes through
  `self._stderr_log_manager` (a `StderrLogManager` instance, already public as an
  instance attribute since `HttpServerLifecycleManager.__init__` assigns it
  unconditionally).

## Design decisions
- Fixture-setup writes (lines 832, 1191, 1204, 1213 — each doing
  `mgr._stderr_log_paths["srv"] = "..."` or similar to seed test state) become direct
  writes to `mgr._stderr_log_manager._log_paths["srv"] = "..."` — this preserves the
  existing white-box-fixture-setup style already used throughout this file (e.g. the
  same tests already write `mgr._stderr_files["srv"] = ...` directly) rather than
  introducing a different setup mechanism for this one field.
- Read-only assertions (lines 455, 483, 1197) become
  `mgr._http_mgr._stderr_log_manager.get_log_path("s") is None` /
  `mgr._stderr_log_manager.get_log_path("srv") is None` — using the new public
  accessor for assertions specifically, per `plans/20260919-211529_plan.md` Testing
  Expectations ("must be updated to assert through the new accessor").

## Alternatives considered
- Write fixture state through `mgr._stderr_log_manager.open_log(...)` (the real,
  non-mocked path) instead of direct dict assignment: rejected — these tests
  deliberately seed minimal fixture state without a real subprocess/file-open flow
  (consistent with how `_stderr_files`/`_http_procs` are seeded elsewhere in the same
  tests), and switching only the stderr-path field to a different setup mechanism
  would make the fixture less uniform, not more.

## Implementation
### Target file
tests/agent/test_lifecycle.py

### Procedure
1. Replace the two read-only assertions at current lines 455 and 483.
2. Replace the fixture-write line at current line 832.
3. Replace the three fixture-write lines at current lines 1191, 1204, 1213, and the
   one read-only assertion at current line 1197.

### Method
Lines 455 and 483 (each inside its own test method, identical replacement in both
places):
```python
assert mgr._http_mgr._stderr_log_manager.get_log_path("s") is None
```

Line 832 (`test_restart_closes_old_stderr_handle`):
```python
mgr._stderr_log_manager._log_paths["srv"] = str(tmp_path / "srv.stderr.log")
```

`TestCleanupServerResources.test_removes_last_health_check_entry` (current lines
1187-1198):
```python
def test_removes_last_health_check_entry(self) -> None:
    mgr = HttpServerLifecycleManager()
    mgr._last_health_check["srv"] = time.monotonic()
    mgr._stderr_files["srv"] = MagicMock()
    mgr._stderr_log_manager._log_paths["srv"] = "/tmp/test.log"

    result = mgr._cleanup_server_resources("srv")

    assert "srv" not in mgr._last_health_check
    assert "srv" not in mgr._stderr_files
    assert mgr._stderr_log_manager.get_log_path("srv") is None
    assert result == ""
```

`test_removes_stderr_file_handle_and_closes_it` (current lines 1200-1207) — replaces
line 1204:
```python
mgr._stderr_log_manager._log_paths["srv"] = "/tmp/test.log"
```

`test_returns_empty_string_when_no_stderr_tail` (current lines 1209-1215) — replaces
line 1213:
```python
mgr._stderr_log_manager._log_paths["srv"] = "/tmp/test.log"
```

### Details
No import changes required — these tests already construct
`HttpServerLifecycleManager()` directly (`mgr._stderr_log_manager` is a
`StderrLogManager` instance created in `__init__`, no new import needed to reach it).

## Compatibility considerations
N/A: test-only file. Each test's asserted behavior (what gets cleared/tracked) is
unchanged — only the attribute path used to observe/seed it changes.

## Security considerations
N/A: test file only.

## Rollback considerations
Revert this file's diff. Depends on Step 02 of this pass being applied first (these
tests will fail against pre-Step-02 source, since `_stderr_log_manager._log_paths`
would then coexist with the still-present `_stderr_log_paths` but the tests would no
longer exercise the latter) — apply in the Plan's stated Phase order
(`plans/20260919-211529_plan.md` Implementation steps, Phase 2).

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py -v` — full file must pass, including
  the 7 updated call sites.
- `rg "_http_mgr\._stderr_log_paths|mgr\._stderr_log_paths" tests/agent/test_lifecycle.py`
  — must return no matches after this change.

## Completion criteria
- All 7 cited call sites use `_stderr_log_manager` (via `.get_log_path()` for
  assertions, via `._log_paths[...]` for fixture writes) instead of
  `_stderr_log_paths`.
- `uv run pytest tests/agent/test_lifecycle.py -v` passes with no new failures.

## Out of scope
- Any other test in this file not listed under Scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation step 1 is itself the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file |

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
- **Requirement ID**: `REQ-001` (update tests asserting against the removed `_stderr_log_paths` attribute)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: tests/agent/test_lifecycle.py
