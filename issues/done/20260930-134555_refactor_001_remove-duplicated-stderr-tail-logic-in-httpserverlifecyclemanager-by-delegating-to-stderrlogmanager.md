# Remove duplicated stderr-tail logic in HttpServerLifecycleManager by delegating to StderrLogManager

## Priority
Medium

## Summary
Replace the private `HttpServerLifecycleManager._read_stderr_tail` implementation with a delegation to `StderrLogManager.read_tail`, eliminating duplicated seek/read logic and aligning the class with its documented composition-facade architecture.

## Background
`scripts/agent/http_lifecycle.py` refactored `HttpServerLifecycleManager` into a composition facade that delegates concern-specific work to six modules (`CommandValidator`, `StderrLogManager`, `ProcessTerminator`, `HealthChecker`, `ProcessSnapshotProvider`, `ShutdownCoordinator`). Its module docstring explicitly states it retains "zero pure-delegation wrappers" and keeps custom logic only for `_read_stderr_tail` (seek/read/decode) and `_wait_exited`.

`StderrLogManager` already owns the canonical stderr-log tail logic via `read_tail` (seek-to-end, size comparison against the configured tail bytes, read, OSError -> empty). `HttpServerLifecycleManager._read_stderr_tail` re-implements the same algorithm directly against the log path instead of calling the owned method.

## Problem
`_read_stderr_tail` duplicates `StderrLogManager.read_tail`: both seek to end, compute `size - tail_bytes`, read the window, and return empty on `OSError`. The two copies can drift apart, and the duplication contradicts the class's own documented contract ("delegating all concern-specific work ... zero pure-delegation wrappers"). A second artifact, the module constant `_STDERR_TAIL_BYTES`, duplicates `StderrLogManager._DEFAULT_STDERR_TAIL_BYTES` and is used only by the duplicated method.

## Reason for Change
- Architecture/reality mismatch: the class claims to delegate all log concerns but keeps one hand-written copy of log-tail logic.
- Maintainability: two sources of truth for the same byte-window algorithm invites divergence.
- Dead constant: `_STDERR_TAIL_BYTES` becomes unused once delegation happens.
- No correctness/security/data-integrity impact today; this is a quality and consistency fix.

## Implementation Intent
Make `HttpServerLifecycleManager` read the stderr tail through `StderrLogManager` instead of opening the file itself. The responsibility ("return the last N decoded bytes of the stderr log") moves entirely to the owning module; the manager should call `self._stderr_log_manager.read_tail(server_key)` and decode the returned bytes. Preserve the observable contract of `_read_stderr_tail`: returns "" when the server key is untracked, decodes with `errors="replace"`, and never raises on `OSError`. Decide internally whether to keep a thin `_read_stderr_tail` wrapper (to satisfy existing test patches) or inline the call and update those tests — prefer removing the wrapper to honor the "zero pure-delegation wrappers" claim, and update tests accordingly.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` (`_read_stderr_tail`, module constant `_STDERR_TAIL_BYTES`, module docstring "Custom logic retained" list)
- `scripts/agent/http_lifecycle_stderr_log_manager.py` (no behavior change expected; reference only)
- `tests/agent/test_http_lifecycle_integration.py` (test sites patching `_read_stderr_tail`)

## Required Changes
- Delete the seek/read/decode body of `_read_stderr_tail` and route it through `self._stderr_log_manager.read_tail(server_key)`, decoding bytes to str with `errors="replace"`.
- Keep the current public contract of `_read_stderr_tail`: "" for untracked keys, empty-string result on `OSError`, no exceptions raised.
- Remove the module-level constant `_STDERR_TAIL_BYTES` if it becomes unreferenced after the change.
- Update the three test sites in `test_http_lifecycle_integration.py` (lines ~907, ~944, ~1033) that patch `type(mgr)._read_stderr_tail` so they exercise the delegated path (patch `StderrLogManager.read_tail`, or adjust), without changing the assertions' intent.
- Update the module docstring's "Custom logic retained in this class" list so it no longer lists `_read_stderr_tail` as retained custom logic (or note it as a thin pass-through if kept).

## Constraints
- Behavior-preserving only: output strings, empty-on-missing semantics, and error suppression must not change.
- Do not alter `StderrLogManager.read_tail` semantics (it remains the single source of truth); only consume it.
- Preserve the `bytes` vs `str` boundary: `read_tail` returns `bytes`; the manager must decode to `str` exactly as before.
- Do not touch unrelated lifecycle methods (`_wait_exited`, start/health-poll/restart/shutdown).

## Acceptance Criteria
- No file-open/seek/read byte-window logic remains in `HttpServerLifecycleManager`; the only tail logic lives in `StderrLogManager.read_tail`.
- `_STDERR_TAIL_BYTES` is removed if unreferenced anywhere in the repo.
- `_read_stderr_tail` (if retained as a wrapper) contains only a single delegation line plus decode; no `open()`/`seek()`.
- Module docstring no longer asserts retained custom seek/read/decode logic that no longer exists.
- All existing `http_lifecycle` tests pass.

## Testing Expectations
- Run the affected suite: `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_stderr_log_manager.py tests/agent/test_lifecycle.py`.
- Confirm the three previously-patched `_read_stderr_tail` sites still validate startup-failure stderr capture (early-exit and timeout paths).
- `uv run ruff check` and `uv run mypy` clean on touched files; `uv run bandit` clean.

## Documentation Impact
Update only the in-code module docstring of `scripts/agent/http_lifecycle.py` (the "Custom logic retained in this class" list) to reflect that stderr-tail reading is now delegated. No `docs/*.md` update required unless the refactor surfaces a new failure/operational note.

## Out of Scope
- Any change to `StderrLogManager.read_tail` behavior, rotation, or config.
- Refactoring other `_read_*`-style helpers, `_wait_exited`, or process-management methods.
- Consolidating other duplicate constants beyond `_STDERR_TAIL_BYTES`.
- Adding new features or changing start/health-poll/restart/shutdown behavior.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Preserve external behavior exactly. Prefer deleting `_read_stderr_tail`'s body and either inlining the delegation in its callers or keeping a one-line wrapper — if you keep the wrapper, update the three test patches; if you delete it, update those patches to target `StderrLogManager.read_tail`. Verify no remaining `open()/seek()` byte-window logic in `HttpServerLifecycleManager`. Run ruff, mypy, bandit, and the listed pytest suites before finishing. Do not modify unrelated lifecycle code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-134555
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_stderr_log_manager.py, tests/agent/test_http_lifecycle_integration.py
