## Goal
- `REQ-001`, `REQ-002`: signal the real process group, resolved with `os.getpgid(proc.pid)`, in `terminate_with_timeout` and `wait_exited` instead of assuming `proc.pid` is a group id.
- `REQ-003`, `REQ-008`: keep the current fallback and the already-exited early return when no group can be resolved.
- `REQ-007`: document the group-leader requirement where the group is resolved.

## Scope
- `scripts/agent/http_lifecycle_process_terminator.py` only: one private helper `_resolve_pgid` (new) and its two call sites. Tests are the other row's document.

## Assumptions
- `terminate_with_timeout` has four callers (the shutdown coordinator once, `http_lifecycle.py` three times), all passing `server_key`; `wait_exited` has no caller in `scripts/`.
- Callers must keep their signatures; the stored `_http_pgids` value is not passed in (Plan A1).
- A non-integer `proc.pid` (for example a `Mock(spec=Popen)`) currently reaches the fallback branch and its warning; `tests/agent/test_http_lifecycle_warning.py` relies on that.

## Design decisions
- `_resolve_pgid` (new) takes the process object and returns `int | None`: `None` when `pid` is missing or not an `int`, or when `os.getpgid(pid)` raises `OSError`; otherwise the group id. Only `OSError` is caught, matching `_get_pgid` in the shutdown coordinator, which is not imported (circular import).
- In `terminate_with_timeout`, when `_resolve_pgid` (new) returns `None`, check `proc.poll()` first: a non-`None` result logs `Process %s already exited` at info level and returns `True`; otherwise the existing fallback block runs unchanged.
- `wait_exited` keeps its `if pgid is None: return False` behavior with the resolved value.

## Alternatives considered
- Read `self._http_pgids[server_key]` from the manager: rejected (changes the manager/terminator interface; Plan A1).
- Reuse `_get_pgid` from the coordinator: rejected (circular import).
- Resolve the group without the `poll()` check: rejected because an exited, reaped process would then warn `children may remain` and call `proc.terminate()`, a behavior change for the default case (`REQ-008`).

## Implementation
### Target file
`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure
- Above `class ProcessTerminator`, add module-level `_resolve_pgid` (new) with a docstring stating that a child is only signaled through its own group when it was started as a group leader (`start_new_session=True` at the launch site in `http_lifecycle.py`), and that `os.getpgid` returns the real group even when it was not (`REQ-007`).
- In `wait_exited`, replace `pgid = getattr(proc, "pid", None)` (line 58) with a call to `_resolve_pgid` (new).
- In `terminate_with_timeout`, replace `pgid = getattr(proc, "pid", None)` (line 84) with a call to `_resolve_pgid` (new). Keep the `if pgid is None or not isinstance(pgid, int)` branch condition.
- Inside that branch, before the existing warning, add the already-exited check: if `proc.poll` exists, call it, and when it returns a value that is not `None`, log the existing `Process %s already exited` info message and `return True`; swallow `OSError`, `AttributeError`, and `TypeError` from the call exactly as the later early-exit block does.

### Method
- Reuse the message and the exception tuple of the existing early-exit block so behavior and wording stay identical; do not change timeouts, `signal` usage, the SIGTERM to SIGKILL order, the `nosec` justifications, or any other warning.
- Keep the `os.killpg(pgid, ...)` calls as they are; only the value of `pgid` changes.

### Details
- Plan line numbers (58, 84) are verified against current source; re-confirm after editing the helper in.
- The helper's `isinstance` check runs before `os.getpgid`, so a `Mock` pid never reaches `os.getpgid` (no `TypeError`).
- Run the broader lifecycle tests (`tests/agent/test_http_lifecycle*.py`, `tests/agent/test_lifecycle.py`, `tests/integration/test_mcp_transport_crash.py`) because other modules call the terminator.

## Compatibility considerations
- For a group leader, `os.getpgid(pid)` equals `pid`, so the signaled group is unchanged. Exited processes keep the early return; a non-integer `pid` keeps the fallback warning. Signatures and return values are unchanged.

## Security considerations
- The change narrows which group receives SIGTERM/SIGKILL (the process's real group instead of an assumed one), removing the chance of signaling an unrelated group when `fields.start_new_session` is false. No new inputs; the `nosec B603` justifications stay accurate.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py tests/agent/test_http_lifecycle_warning.py tests/agent/test_http_lifecycle_shutdown_coordinator.py tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle.py tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_health_check.py tests/integration/test_mcp_transport_crash.py -v`
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/agent/http_lifecycle_process_terminator.py -c pyproject.toml`, `uv run vulture scripts/agent/http_lifecycle_process_terminator.py --min-confidence 80`, `uv run radon cc scripts/agent/http_lifecycle_process_terminator.py -s`
- `uv run python tools/check_suppression_justification.py`

## Completion criteria
- Both methods resolve the group through the helper, and the already-exited early return is in place.
- The lifecycle test modules above pass, including the existing `Mock(spec=Popen)` warning test, unchanged.
- Lint, type, architecture, and security checks report no new findings; the full suite shows no new failure.
- No `docs/*.md` change is needed (Plan Documentation Impact is N/A).

## Out of scope
- `http_lifecycle.py`, the shutdown coordinator, timeouts, escalation order, any manager/terminator interface change, any compatibility shim, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_resolve_pgid` (new) and use it in `wait_exited` and `terminate_with_timeout` | Completed | 20261016-122241 | 20261016-122241 | changed: scripts/agent/http_lifecycle_process_terminator.py; helpers _resolve_pgid and _already_exited (existing early-exit block now reuses _already_exited, same behavior) code change reverted (Rollback on Failure): broke 2 tests in tests/agent/test_lifecycle.py changed: scripts/agent/http_lifecycle_process_terminator.py (helpers _resolve_pgid, _already_exited) |
| 2 | Add the already-exited early return and the group-leader docstring | Completed | 20261016-122241 | 20261016-122241 | already-exited early return + group-leader docstring added in the same edit reverted together with step 1 already-exited early return and group-leader docstring added in the same edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the broader lifecycle tests | Completed | 20261016-122802 | 20261016-122802 | Blocked: additional target file discovered - tests/agent/test_lifecycle.py unblocked: plan amended, procedure 03 added ruff/mypy/lint-imports/bandit/vulture/suppression/reference-table clean; 8 lifecycle modules 133 passed (run after 02 and 03); full suite 8429 passed 0 failed; diff-cover 100% (24 lines); docs N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Additional target file discovered: `tests/agent/test_lifecycle.py` (`TestProcessGroupShutdown::test_terminate_sigkill_on_second_timeout`, `::test_terminate_never_uses_thread_even_when_process_never_exits`) use fake pids 55/77 and patch only `os.killpg`; with the fix the real `os.getpgid` raises `ProcessLookupError`, so no signal is sent. Code change reverted. The Plan must add this file as a target (or choose another approach) before re-running. | Yes: plan amended (REQ-009) and procedure 03 generated | 20261016-122229 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002 (true group resolution), REQ-003, REQ-008 (fallback and exited early return), REQ-004, REQ-005 (no behavior change otherwise), REQ-007 (group-leader documentation)
- **Source issue**: issues/20261016-092918_mcp002_terminator_pgid_wrong_group_kill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-102005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-120754
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py