## Goal
Update every assertion/fixture-setup in this file that reads or writes
`HttpServerLifecycleManager._stderr_log_paths` directly, so the file keeps testing the
same behavior after Step 02 of this pass removes that attribute (`REQ-001`).

## Scope
- In scope: the 8 call sites confirmed by `rg "_stderr_log_paths" tests/agent/test_http_lifecycle_integration.py`:
  - line 225 (fixture write, `test_shutdown_all_clears_stderr_log_paths`)
  - line 233 (assertion, same test)
  - line 442 (assertion, a getpgid-failure test in the `TestStart` area)
  - line 484 (fixture write, `test_restart_clears_stderr_file`)
  - line 500 (assertion, same test)
  - line 566 (fixture write, `test_get_process_info_returns_snapshot`)
  - line 716 (fixture write, `test_shutdown_all_clears_all_state_even_if_some_failures`)
  - line 728 (assertion, same test)
- Out of scope: any other test in this file; the semantics each test verifies are
  unchanged — only the attribute path used to observe/seed the tracked stderr path
  changes.

## Assumptions
- Step 02 of this pass
  (`implementations/20260919-212015_02_scripts_agent_http_lifecycle.py.md`) removes
  `HttpServerLifecycleManager._stderr_log_paths` and routes all reads/writes through
  `self._stderr_log_manager` (a `StderrLogManager` instance, an unconditional
  `HttpServerLifecycleManager.__init__` assignment).

## Design decisions
- Fixture-setup writes (lines 225, 484, 566, 716) become direct writes to
  `mgr._stderr_log_manager._log_paths["..."] = "..."`, matching this file's existing
  convention of seeding other tracking dicts (`_http_procs`, `_http_pgids`,
  `_stderr_files`) via direct assignment.
- Read-only assertions (lines 233, 442, 500, 728) become
  `mgr._stderr_log_manager.get_log_path("test") is None`, per
  `plans/20260919-211529_plan.md` Testing Expectations ("must be updated to assert
  through the new accessor"). Each of these 4 tests only ever tracks the single key
  `"test"`, so asserting that key is now untracked is equivalent to the original
  `len(...) == 0` / `.get(...) is None` checks — no loss of test coverage.

## Alternatives considered
- Keep `len(mgr._stderr_log_manager._log_paths) == 0` style assertions instead of
  `get_log_path("test") is None`: considered for lines 233/728 specifically (both
  originally asserted `len(...) == 0`, a slightly broader "nothing at all is tracked"
  claim than "this one key is gone"). Rejected in favor of `get_log_path` per the
  Plan's explicit instruction to assert through the new accessor, and because each
  test's fixture only ever adds the single `"test"` key, so the two forms are
  equivalent in what they actually verify for these tests.

## Implementation
### Target file
tests/agent/test_http_lifecycle_integration.py

### Procedure
1. Replace the fixture-write/assertion pair at current lines 225/233
   (`test_shutdown_all_clears_stderr_log_paths`).
2. Replace the assertion at current line 442.
3. Replace the fixture-write/assertion pair at current lines 484/500
   (`test_restart_clears_stderr_file`).
4. Replace the fixture-write at current line 566
   (`test_get_process_info_returns_snapshot`).
5. Replace the fixture-write/assertion pair at current lines 716/728
   (`test_shutdown_all_clears_all_state_even_if_some_failures`).

### Method
`test_shutdown_all_clears_stderr_log_paths` (current lines 221-233):
```python
async def test_shutdown_all_clears_stderr_log_paths(self) -> None:
    manager = HttpServerLifecycleManager()
    manager._http_procs["test"] = Mock(poll=Mock(return_value=0))
    manager._stderr_log_manager._log_paths["test"] = "/tmp/test.log"

    with (
        patch.object(signal, "getsignal", return_value=signal.default_int_handler),
        patch.object(signal, "signal", side_effect=lambda sig, h: h),
    ):
        await manager.shutdown_all()

    assert manager._stderr_log_manager.get_log_path("test") is None
```

Line 442 (assertion inside a getpgid-failure test):
```python
assert mgr._stderr_log_manager.get_log_path("test") is None
```

`test_restart_clears_stderr_file` (current lines 480-500), replacing line 484 and
line 500:
```python
mgr._stderr_log_manager._log_paths["test"] = "/tmp/test.log"
```
```python
assert mgr._stderr_log_manager.get_log_path("test") is None
```

Line 566 (fixture write inside `test_get_process_info_returns_snapshot`):
```python
mgr._stderr_log_manager._log_paths["test"] = "/tmp/test.stderr.log"
```

`test_shutdown_all_clears_all_state_even_if_some_failures` (current lines 710-728),
replacing line 716 and line 728:
```python
mgr._stderr_log_manager._log_paths["test"] = "/tmp/test.log"
```
```python
assert mgr._stderr_log_manager.get_log_path("test") is None
```

### Details
No import changes required — these tests already construct
`HttpServerLifecycleManager()` (or receive it via the `mgr` fixture); accessing
`._stderr_log_manager` needs no new import.

## Compatibility considerations
N/A: test-only file. Each test's asserted behavior is unchanged — only the attribute
path used to observe/seed the tracked stderr path changes.

## Security considerations
N/A: test file only.

## Rollback considerations
Revert this file's diff. Apply after Step 02 of this pass (per
`plans/20260919-211529_plan.md` Implementation steps, Phase 2) — these tests will
fail against pre-Step-02 source.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` — full file must
  pass, including the 8 updated call sites.
- `rg "\.\_stderr_log_paths" tests/agent/test_http_lifecycle_integration.py` — must
  return no matches after this change.

## Completion criteria
- All 8 cited call sites use `_stderr_log_manager` (via `.get_log_path()` for
  assertions, via `._log_paths[...]` for fixture writes) instead of
  `_stderr_log_paths`.
- `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` passes with no new
  failures.

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
- **Related target files**: tests/agent/test_http_lifecycle_integration.py
