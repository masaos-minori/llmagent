## Goal

Make the killpg-failure test actually exercise the killpg path, and drop the `_http_pgids` patch that row 3 removes (REQ-001, REQ-010; AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan's `R3-ownership` unit lists Phases 3 and 4; this row is cited by Phase 3)

## Assumptions

- `ProcessTerminator._resolve_pgid` (`scripts/agent/http_lifecycle_process_terminator.py:57-73`) resolves the group id with `os.getpgid(proc.pid)` and returns `None` for a non-integer pid; the terminator module never reads a manager tracking dict.
- `proc_mock = Mock(spec=subprocess.Popen)` (`:89-91`) leaves `proc_mock.pid` a `Mock`, so `_resolve_pgid` returns `None` today and the test takes the no-pgid fallback branch (`:234-245`) despite its docstring.
- `_assert_unconfirmed_termination_line` (`:46-61`) filters on the exact substring `"proc.terminate() fallback"`, which only the no-pgid branch emits (`:240`); the killpg-failure branch emits `"os.killpg(SIGTERM) failed ... falling back to proc.terminate()"` (`:259-264`).

## Design decisions

- Delete the patch instead of retargeting it to the record registry: it has no effect on the code under test, and a registry-patched version would keep a second inert fixture while implying the terminator reads the registry.
- Drive the killpg path through `os.getpgid` (`proc_mock.pid = 4242`, `patch.object(os, "getpgid", return_value=1234)`), because that is the only input the terminator uses to choose the group-signalling branch.

## Alternatives considered

- Keep the test asserting the fallback line and only remove the patch — rejected: the file's docstring claims it verifies the killpg failure, and REQ-010's manual-cleanup message depends on that branch's pid/pgid line being a warning.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_warning.py`
### Procedure
1. Remove `patch.object(mgr, "_http_pgids", {"test-server": 1234})` from `test_terminate_warning_when_killpg_fails` (`:97`).
2. Give the fixture an integer pid and patch `os.getpgid` so the group-signalling branch is reached.
3. Assert the killpg-failure warning line and the outcome instead of reusing the fallback-line helper.
### Method
One test function rewritten (`:87-107`); the other three tests in the file (`:64-84`, `:110-131`) are untouched.

### Details

- Fixture: `proc_mock.pid = 4242`; `patch.object(os, "getpgid", return_value=1234)`; keep `patch.object(os, "killpg", side_effect=OSError("No such process"))` — in this branch `os.killpg` is called once, with `signal.SIGTERM` (`:253`), before the function returns.
- Assertions: `outcome is TerminationOutcome.EXIT_UNCONFIRMED` (the fallback `proc.terminate()` succeeded, exit not observed); exactly one captured warning contains `"os.killpg(SIGTERM) failed"`, `"pid=4242"`, `"pgid=1234"`; `capture.at_error_or_worse()` stays empty, matching the file's non-fatal rule (`:59-60`).
- Keep the docstring accurate: the test verifies the SIGTERM-group failure warning and the `proc.terminate()` fallback that follows it.
- `mgr` is still needed for the fixture's terminator (`mgr._process_terminator`), so the `HttpServerLifecycleManager()` construction at `:89` stays.

## Compatibility considerations

- This is the only `patch.object` against `_http_pgids` in `tests/` (checked across `tests/`), so it is the only test that breaks structurally — not just semantically — when row 3 removes the attribute.
- `tools/check_mock_patch_targets.py` runs on changed `patch(...)` calls in `tests/`; the new `patch.object(os, "getpgid", ...)` targets the module the terminator calls directly (`scripts/agent/http_lifecycle_process_terminator.py:71`), so it takes effect.

## Security considerations

N/A: test-only change; no signal is actually sent (`os.killpg` is patched).

## Rollback considerations

Revert this row together with row 3: the patch removal only makes sense once `_http_pgids` no longer exists.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_warning.py` — green before and after this row (the rewritten test passes against the current terminator, which already resolves pgid through `os.getpgid`).
- `uv run python tools/check_mock_patch_targets.py` per `rules/tool-gates.md`.
- `uv run ruff check tests/agent/test_http_lifecycle_warning.py` per `rules/toolchain.md`.

## Completion criteria

- No reference to `_http_pgids` remains in the file.
- `test_terminate_warning_when_killpg_fails` reaches the group-signalling branch and asserts its pid/pgid warning line.

## Out of Scope

- The record registry itself (rows 2-3).
- The other tests in this file, which already exercise the no-pgid fallback path.
- `ProcessTerminator` implementation (`scripts/agent/http_lifecycle_process_terminator.py`), which this Plan does not change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-132200 | 20261126-132142 | _http_pgids patch removed; killpg branch driven via proc_mock.pid=4242 + os.getpgid patch; killpg-failure warning line asserted |
| 2 | Add or update tests per Validation plan | Completed | 20261126-132200 | 20261126-132142 | Existing test rewritten in place; other three tests untouched |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-132300 | 20261126-132142 | pytest 3 passed; ruff check/format clean; check_mock_patch_targets: no findings |
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
- **Requirement ID**: `REQ-001` (patch removal once the dict is gone), `REQ-010` (manual-cleanup warning line)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-000128
- **Related target files**: `tests/agent/test_http_lifecycle_warning.py`