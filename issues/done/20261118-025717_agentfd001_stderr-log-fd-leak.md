# `StderrLogManager._log_files` holds unclosed handles and is a dead store

## Priority
Low

## Summary
`StderrLogManager` in `http_lifecycle_stderr_log_manager.py` keeps an internal `_log_files` dict of open stderr file handles that is written but never read, is never closed on rotation/forget/clear, and is leaked through `rotate_log`'s `os.rename`. Remove the dead store, close handles on every cleanup path, and close the handle before rotating.

## Background
`StderrLogManager` manages stderr log files for HTTP-subprocess MCP servers. `HttpServerLifecycleManager` delegates all stderr-log operations to it. `open_log(server_key, cfg)` opens a file in append mode, stores the returned handle in `self._log_files[server_key]`, records the path in `self._log_paths[server_key]`, and returns the handle to the caller. The launcher (`http_lifecycle_subprocess_launcher.py`) receives that returned handle and owns it for the subprocess's stderr. A prior refactor (`issues/done/20260919-210241_refactor_003_...md`) addressed duplication of the `_stderr_log_paths` tracking dict in `http_lifecycle.py`, which is a different attribute and does not touch `_log_files` here.

## Problem
- `_log_files` is written in `open_log` but never read anywhere in the repository. It is a dead store that only holds resource-bearing objects.
- The handles stored in `_log_files` are never closed. `forget(server_key)` and `clear()` only mutate `_log_paths` (`.pop` / `.clear`); they do not close the corresponding `_log_files` handles, so every tracked server leaks one open file descriptor until garbage collection.
- `rotate_log(server_key, max_bytes)` renames the active log to `<path>.old` via `os.rename` without closing the still-open handle first. The open handle keeps the renamed `.old` file open and growing, and the rotation neither closes nor rebinds it.

## Reason for Change
The dead `_log_files` store is misleading: a reader assumes the manager tracks live handles, but it never uses them. More importantly, the missing close on `forget`/`clear`/`rotate_log` leaks file descriptors across server start/stop and rotation cycles in the long-running agent process. Removing the dead store and adding closes on every cleanup path fixes the leak and removes the confusion.

## Implementation Intent
Decide whether `_log_files` is needed at all. The launcher already owns the handle via the return value of `open_log`, so if nothing else reads `_log_files`, remove the attribute and its write in `open_log`. If the manager must retain a handle for its own bookkeeping, close every stored handle in `forget` (single key) and `clear` (all keys), wrapping close in a guard so a already-closed or missing handle does not raise. In `rotate_log`, close the tracked handle before `os.rename` so the rotated file is fully released. Preserve the public behavior of `read_tail`, `rotate_log`'s return value, and `get_log_path`.

## Target Files or Areas
- `scripts/agent/http_lifecycle_stderr_log_manager.py` (`StderrLogManager`)
- `tests/agent/` tests covering `StderrLogManager`

## Required Changes
- Remove the unused `_log_files` dict and its write in `open_log`, OR close stored handles on every cleanup path if the store is retained.
- Close the handle for a key in `forget`; close all handles in `clear`.
- Close the tracked handle before `os.rename` in `rotate_log`.
- Add tests asserting handles are closed after `forget`/`clear`/`rotate_log`.

## Constraints
- Do not change the handle ownership contract: `open_log` must still return the open handle for the launcher to use.
- Closing must not break an in-flight `read_tail` (which re-opens the path itself and does not use the stored handle).
- Guard against double-close; do not raise if a handle is already closed or absent.

## Acceptance Criteria
- No open file handle is left unclosed by `forget`, `clear`, or `rotate_log`.
- `rotate_log` releases the underlying handle when it renames the file.
- Existing `StderrLogManager` tests pass unmodified in intent.

## Testing Expectations
- Unit: assert that after `forget`/`clear`/`rotate_log` the relevant file object's `closed` flag is `True` (use a fake/in-memory file object whose close is observable).
- Run the affected `tests/agent` paths and confirm no regression.
- `uv run ruff check` and `uv run mypy` clean on the changed file.

## Documentation Impact
None expected.

## Out of Scope
- Any change to `http_lifecycle.py`'s `_stderr_log_paths` handling (out of scope; owned by `HttpServerLifecycleManager`).
- Changing how the launcher consumes the handle returned by `open_log`.

## Dependencies
N/A: none

## Unresolved Questions
- Whether anything outside `http_lifecycle_stderr_log_manager.py` reads `StderrLogManager._log_files`; confirm with a repository-wide search before removing the attribute. If the launcher or lifecycle manager needs the handle for shutdown, retain it with a proper close path instead of deleting it.

## AI Implementation Instruction
Read `http_lifecycle_stderr_log_manager.py` and grep the whole repository for `_log_files` before editing. Confirm nothing reads `_log_files`; if truly unused, delete the attribute and its write in `open_log`. If it must be retained, add guarded close calls in `forget`, `clear`, and before `os.rename` in `rotate_log`. Do not change `open_log`'s return value or `read_tail`'s re-open behavior. Add an observable-close test. Stop and report if a reader of `_log_files` exists that the grep missed.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-025717
- **Related target files**: `scripts/agent/http_lifecycle_stderr_log_manager.py`
