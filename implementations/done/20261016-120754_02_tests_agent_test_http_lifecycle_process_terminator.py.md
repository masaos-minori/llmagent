## Goal
- `REQ-006`, `REQ-008`: add regression tests for the true-group resolution, the no-group fallback, the already-exited early return, and the non-integer `pid` case in `ProcessTerminator`.

## Scope
- Additions to `tests/agent/test_http_lifecycle_process_terminator.py` only. The code change is the other row's document (`scripts/agent/http_lifecycle_process_terminator.py`).

## Assumptions
- Existing tests patch the whole `os` and `time` names inside `agent.http_lifecycle_process_terminator` and set `proc.pid = 12345`; their `mock_os.getpgid.return_value = 12345` is unused today and becomes used after the fix.
- With the whole `os` patched, builtin exceptions such as `OSError` and `ProcessLookupError` still work as `side_effect` values.

## Design decisions
- Follow the neighbouring class style: `MagicMock` proc, `patch("agent.http_lifecycle_process_terminator.os")`, and `patch("agent.http_lifecycle_process_terminator.time")` with a two-value `monotonic` side effect.
- One new test class for the new behavior; the two existing tests stay unchanged (they show the group-leader case is unaffected).

## Alternatives considered
N/A: a real subprocess with `start_new_session=False` was rejected as slower and platform-dependent for a unit test.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_process_terminator.py`

### Procedure
- Add class `TestProcessTerminatorPgidResolution` (new) with these async tests:
- `test_killpg_targets_resolved_group_when_pid_differs` (new): `proc.pid = 12345`, `proc.poll.return_value = None`, `mock_os.getpgid.return_value = 777`, `mock_os.killpg.side_effect = [None, None]`, `time.monotonic` returning `0.0` then `10.0`; assert both `killpg` calls use `777` and the signals are SIGTERM then 9.
- `test_wait_exited_uses_resolved_group` (new): `getpgid` returns `777`, `killpg` raises `ProcessLookupError`; assert `wait_exited` returns `True` and `killpg` was called with `(777, 0)`.
- `test_unresolvable_pgid_falls_back_to_proc_terminate` (new): `getpgid` raises `OSError`, `poll` returns `None`; assert the result is `True`, `proc.terminate` was called once, and `killpg` was not called.
- `test_already_exited_process_returns_true_without_terminate` (new): `getpgid` raises `ProcessLookupError`, `poll` returns `0`; assert the result is `True`, `proc.terminate` was not called, and `killpg` was not called.
- `test_non_integer_pid_takes_fallback_without_raising` (new): proc built as `MagicMock` with a non-integer `pid` (a `MagicMock` attribute) and `poll` returning `None`; assert no exception, `proc.terminate` called once, and `getpgid` not called.
- Added at execution time to reach the 90% diff-coverage gate (the already-exited helper's branches): `test_resolved_group_with_exited_process_returns_true` (new) (group resolved, `poll()` returns an exit code: `True`, no `killpg`, no `proc.terminate()`), `test_poll_error_is_treated_as_still_running` (new) (`poll()` raises `OSError`: escalation proceeds with SIGTERM to the resolved group), and `test_proc_without_poll_is_treated_as_still_running` (new) (no `poll` attribute: escalation proceeds).

### Method
- Use `@pytest.mark.asyncio` like the existing tests; use `call_args_list` positional arguments for the signal and group assertions.
- Import `ProcessLookupError` needs nothing (builtin); add no new third-party imports.

### Details
- Run the new tests against the unfixed module first: the two that check the resolved group must fail, the fallback and already-exited ones are expected to fail or behave differently, and the non-integer pid one documents preserved behavior and should already pass. Record the observed result in the Notes of the Execution Status row.
- Tests use mocks only and never signal a real process.

## Compatibility considerations
N/A: additive tests; no existing test is edited.

## Security considerations
N/A: test-only change; `os.killpg` is always mocked so no real process group is signaled.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -v` (new tests fail before and pass after the code change; the two existing tests pass throughout)
- `uv run ruff format tests/agent/test_http_lifecycle_process_terminator.py`, `uv run ruff check tests/agent/test_http_lifecycle_process_terminator.py`, `uv run mypy --no-namespace-packages tests/agent/test_http_lifecycle_process_terminator.py` (compare to the baseline error count)
- `uv run python tools/check_mock_patch_targets.py`
- `uv run coverage run -m pytest tests/agent/test_http_lifecycle_process_terminator.py`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- The five new tests exist and pass after the code change; the tests that exercise the new resolution fail beforehand.
- The two existing tests pass unchanged.
- No new mypy error in the file; the diff-cover report covers the changed lines of the terminator, or its gap is recorded in Notes.

## Out of scope
- Other test modules, `http_lifecycle.py`, the shutdown coordinator, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the pgid resolution test class and its five tests | Completed | 20261016-122250 | 20261016-122802 | changed: tests/agent/test_http_lifecycle_process_terminator.py; 8 tests added (5 planned + 3 for diff-coverage) |
| 2 | Run the new tests against the unfixed module and record the result | Completed | 20261016-122802 | 20261016-122802 | red check on HEAD module: 3 failed (resolved group x2, unresolvable fallback), 4 passed (preserved behavior: exited, non-integer pid, existing tests) |
| 3 | Run the validation sequence (`rules/toolchain.md`) after the code change | Completed | 20261016-122802 | 20261016-122802 | ruff clean; mypy clean (baseline clean); check_mock_patch_targets clean; diff-cover 100% |

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
- **Requirement ID**: REQ-006 (regression tests), REQ-008 (already-exited and non-integer pid behavior)
- **Source issue**: issues/20261016-092918_mcp002_terminator_pgid_wrong_group_kill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-102005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-120754
- **Related target files**: tests/agent/test_http_lifecycle_process_terminator.py