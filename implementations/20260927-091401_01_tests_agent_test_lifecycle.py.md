## Goal

Fix 17 references to `HttpServerLifecycleManager`'s removed `_open_stderr_log`/`_terminate_with_timeout` wrapper methods in `tests/agent/test_lifecycle.py` (12 failing tests across `TestHttpLifecycleStderrLog`, `TestProcessGroupShutdown`, `TestHttpManagerRestart`, `TestStartHttpSubprocess`), redirecting each to the current component-delegated targets (`self._stderr_log_manager.open_log`, `self._process_terminator.terminate_with_timeout`) (REQ-001).

## Scope

In scope: all 17 `_open_stderr_log`/`_terminate_with_timeout` references in this file (direct calls, `monkeypatch.setattr`, `patch.object`, attribute assignments). Out of scope: `scripts/agent/http_lifecycle.py` and its extracted component modules — the refactor removing these wrapper methods (commit `d98dda9a`) is intentional and already complete; no production change.

## Assumptions

- `StderrLogManager.open_log(self, server_key: str, cfg: object) -> IO[bytes]`'s signature matches the existing `_patch_open_to_tmp` helper's `patched_open(self, server_key, cfg=None)` closely enough that only the `self` type and the internal `self._stderr_log_manager._log_paths[...]` → `self._log_paths[...]` access need adjusting once `self` becomes a `StderrLogManager` instance directly.
- `mgr._subprocess_mgr._http_mgr` (used at 2 call sites) resolves to a real `HttpServerLifecycleManager` instance via `_ServerLifecycleRouter` → `_SubprocessLifecycleManager._http_mgr` (confirmed via Read of `scripts/agent/factory.py:90,182`), so the same `_process_terminator.terminate_with_timeout` fix applies there too.

## Design decisions

- Follow the exact fix pattern already applied to the sibling test file `tests/agent/test_http_lifecycle_warning.py` in the same original commit (`d98dda9a`): `mgr._terminate_with_timeout(proc, key, timeout=1.0)` → `mgr._process_terminator.terminate_with_timeout(proc, key, timeout=1.0)`.
- Restructure the class-level `monkeypatch.setattr(HttpServerLifecycleManager, "_open_stderr_log", patched_open)` helper (`_patch_open_to_tmp`, line ~107) into `monkeypatch.setattr(StderrLogManager, "open_log", patched_open_log)`, adjusting `patched_open`'s `self` type and its internal `self._stderr_log_manager._log_paths[server_key] = str(log_path)` line to `self._log_paths[server_key] = str(log_path)` (since `self` is now the `StderrLogManager` instance directly, not the outer manager).

## Alternatives considered

- Leaving `_patch_open_to_tmp`'s class-level patch target unchanged and instead patching per-instance (`patch.object(mgr._stderr_log_manager, "open_log", ...)`) at each of the 6 `TestHttpLifecycleStderrLog` call sites individually: rejected — the existing class-level helper pattern is simpler to adapt (one change) than converting every call site to instance-level patching.

## Implementation

### Target file

`tests/agent/test_lifecycle.py`

### Procedure

1. Re-confirm each of the 17 references' exact current line/form via `rg -n "_open_stderr_log|_terminate_with_timeout" tests/agent/test_lifecycle.py` (adversarial re-verification — line numbers may have shifted since the Plan was written).
2. Restructure `_patch_open_to_tmp`'s `patched_open` function and its `monkeypatch.setattr(...)` call (currently ~1 helper, used by `TestHttpLifecycleStderrLog`'s 6 tests) to target `StderrLogManager.open_log` instead of `HttpServerLifecycleManager._open_stderr_log`.
3. For each of the remaining `_terminate_with_timeout` references (direct calls at lines ~990, 1013, 1043, 1075, 1101; `patch.object`/`monkeypatch.setattr`/direct-assignment forms at lines ~275, 335, 545, 848, 865, 876, 913, 967), replace the target with `._process_terminator.terminate_with_timeout` on the same manager instance (`mgr`, or `mgr._subprocess_mgr._http_mgr` where that's the existing access path).

### Method

Mechanical reference-target replacement across 17 call sites, following the already-landed sibling-file fix pattern (`tests/agent/test_http_lifecycle_warning.py`, commit `d98dda9a`) — no new test logic, only redirecting existing mocks/calls to the current component-delegated API surface.

### Details

- `StderrLogManager.open_log(self, server_key: str, cfg: object) -> IO[bytes]` (`scripts/agent/http_lifecycle_stderr_log_manager.py`) is the replacement target for `_open_stderr_log`.
- `ProcessTerminator.terminate_with_timeout(self, proc: object, server_key: str, timeout: float = 5.0) -> None` (`scripts/agent/http_lifecycle_process_terminator.py:71-73`) is the replacement target for `_terminate_with_timeout`.
- Reference fix already landed: `tests/agent/test_http_lifecycle_warning.py`'s diff in commit `d98dda9a` (`await mgr._terminate_with_timeout(...)` → `await mgr._process_terminator.terminate_with_timeout(...)`).
- After the restructure, confirm `_patch_open_to_tmp`'s docstring/comments (if any) still accurately describe the patch target.

## Compatibility considerations

- No production code changes; test-only fix restoring compatibility with the already-shipped composition-facade refactor (commit `d98dda9a`).

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- To rollback: `git revert` the commit containing this change, restoring the prior (broken) references. No data migration or state involved.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_lifecycle.py` | Unit | `uv run pytest tests/agent/test_lifecycle.py -q` | All tests pass, including the 12 previously-failing ones |

## Completion criteria

- `uv run pytest tests/agent/test_lifecycle.py -q` passes with no failures.
- Each fixed test's original stderr-log-capture/process-termination assertion is genuinely exercised (confirmed by the test passing for the right reason, not by relaxing any assertion).

## Out of scope

- `tests/integration/test_mcp_transport_crash.py` (covered by its own implementation procedure document from this same Plan).
- `scripts/agent/http_lifecycle.py` and its component modules (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no new test needed — fixing the existing references is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: fix `_open_stderr_log`/`_terminate_with_timeout` references in `tests/agent/test_lifecycle.py`
- **Source issue**: issues/20260927-075239_agent002_httpserverlifecyclemanager-missing-lifecycle-methods-tests-reference.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-081423_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091401
- **Related target files**: tests/agent/test_lifecycle.py
