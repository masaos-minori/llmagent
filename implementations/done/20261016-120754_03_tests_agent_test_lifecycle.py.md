## Goal
- `REQ-009`: make the four `TestProcessGroupShutdown` tests that patch only `os.killpg` resolve the group through `os.getpgid` explicitly, so they keep passing, deterministically, once `ProcessTerminator` resolves the group with `os.getpgid(proc.pid)`.

## Scope
- Four existing tests in `tests/agent/test_lifecycle.py::TestProcessGroupShutdown`: `test_terminate_uses_killpg_sigterm`, `test_terminate_fallback_on_process_lookup_error`, `test_terminate_sigkill_on_second_timeout`, and `test_terminate_never_uses_thread_even_when_process_never_exits`. The already-exited test in the same class is not touched.

## Assumptions
- These tests use fake pids (42, 42, 55, 77) and assert on those same values as group ids, so returning the pid itself from a patched `os.getpgid` preserves every assertion.
- `mod.os` in these tests is the real `os` module, so `monkeypatch.setattr(mod.os, "getpgid", ...)` is undone at test teardown.

## Design decisions
- Add one `monkeypatch.setattr(mod.os, "getpgid", lambda pid: pid)` line right after each test's existing `killpg` patch, matching how the same tests already patch `killpg`.
- Leave assertions, timeouts, and helper functions as they are.

## Alternatives considered
N/A: patching `os.getpgid` inside a shared fixture was rejected as a larger change than four added lines in the existing tests.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
- In each of the four tests named in Scope, add the `getpgid` patch after the `killpg` patch.
- For `test_terminate_fallback_on_process_lookup_error`, add it before the call to `terminate_with_timeout` so the `killpg` path (which raises `ProcessLookupError`) is still the one exercised.

### Method
- Use the same `monkeypatch` argument the tests already take; the lambda returns its argument unchanged.
- Keep line length at 88 characters or fewer; wrap the call like the neighbouring `killpg` patches.

### Details
- Cycles run in filename order, so this document runs after the two before it; the code and test changes are validated together once all three are applied (the broad lifecycle run in the first document belongs after this one).
- Confirm that the two tests that failed with the fix (`test_terminate_sigkill_on_second_timeout` and `test_terminate_never_uses_thread_even_when_process_never_exits`) pass after this change, and that the whole file passes.

## Compatibility considerations
N/A: test-only change; every assertion is kept.

## Security considerations
N/A: test-only change; `os.killpg` stays mocked so no real process group is signaled.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py -v`
- `uv run ruff format tests/agent/test_lifecycle.py`, `uv run ruff check tests/agent/test_lifecycle.py`, `uv run mypy --no-namespace-packages tests/agent/test_lifecycle.py` (compare against the baseline error count)
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The four tests patch `os.getpgid` and pass with the terminator fix applied; the rest of the file passes unchanged.
- No new mypy or lint finding in the file.

## Out of scope
- The other tests in the file, the terminator, `http_lifecycle.py`, and `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `os.getpgid` patch to the four killpg-only tests | Completed | 20261016-122318 | 20261016-122802 | changed: tests/agent/test_lifecycle.py (4 getpgid patches) |
| 2 | Run the validation sequence (`rules/toolchain.md`) after the code change | Completed | 20261016-122802 | 20261016-122802 | ruff clean; mypy 10 errors identical to baseline; the 2 previously failing tests pass; file 63 passed |

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
- **Requirement ID**: REQ-009 (killpg-only tests resolve the group through `os.getpgid`)
- **Source issue**: issues/20261016-092918_mcp002_terminator_pgid_wrong_group_kill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-102005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-120754
- **Related target files**: tests/agent/test_lifecycle.py